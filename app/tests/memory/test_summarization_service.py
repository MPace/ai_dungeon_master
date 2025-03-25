"""
Tests for the Summarization Service
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.summarization_service import SummarizationService

class TestSummarizationService:
    """Test suite for SummarizationService"""

    @pytest.fixture
    def mock_pipeline(self):
        """Mock Hugging Face pipeline"""
        with patch('transformers.pipeline') as mock_pipeline:
            # Configure the mock pipeline to return predictable summaries
            mock_instance = MagicMock()
            mock_pipeline.return_value = mock_instance
            
            # Configure mock to return a list of dict with summary_text
            mock_instance.return_value = [{'summary_text': 'This is a summarized version of the text.'}]
            
            yield mock_pipeline

    @pytest.fixture
    def mock_db(self):
        """Mock MongoDB connection"""
        with patch('app.extensions.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_db.memory_vectors = mock_collection
            mock_get_db.return_value = mock_db
            yield mock_db

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock EmbeddingService"""
        with patch('app.extensions.get_embedding_service') as mock_get_service:
            mock_service = MagicMock()
            # Configure the mock to return predictable embeddings
            mock_service.generate_embedding.return_value = [0.1] * 384
            mock_get_service.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def summarization_service(self, mock_pipeline):
        """Create a SummarizationService with mocked pipeline"""
        service = SummarizationService(model_name="facebook/bart-large-cnn")
        return service

    def test_initialization(self, mock_pipeline):
        """Test SummarizationService initialization"""
        service = SummarizationService(model_name="facebook/bart-large-cnn")
        assert service is not None
        assert service.model_name == "facebook/bart-large-cnn"
        assert service.summarizer is not None
        assert mock_pipeline.called
        assert mock_pipeline.call_args[1]['model'] == "facebook/bart-large-cnn"

    def test_summarize_text(self, summarization_service):
        """Test summarizing a single text"""
        # Setup
        text = "This is a long text that needs to be summarized. " * 20
        
        # Call the function
        summary = summarization_service.summarize_text(text, max_length=50, min_length=10)
        
        # Verify
        assert summary == "This is a summarized version of the text."
        assert summarization_service.summarizer.called
        assert summarization_service.summarizer.call_args[0][0] == text
        assert summarization_service.summarizer.call_args[1]['max_length'] == 50
        assert summarization_service.summarizer.call_args[1]['min_length'] == 10

    def test_summarize_text_too_long(self, summarization_service):
        """Test summarizing very long text gets truncated"""
        # Setup
        text = "X" * 2000  # Text longer than the 1024 limit
        
        # Call the function
        summarization_service.summarize_text(text)
        
        # Verify the text was truncated
        assert len(summarization_service.summarizer.call_args[0][0]) <= 1024

    def test_summarize_text_model_failure(self, summarization_service):
        """Test fallback when model fails"""
        # Setup - make summarizer raise an exception
        summarization_service.summarizer.side_effect = Exception("Model error")
        
        # Call the function
        text = "This text will cause an error in the model."
        summary = summarization_service.summarize_text(text)
        
        # Verify - it should return the original text as fallback
        assert summary == text

    def test_summarize_memories(self, summarization_service, mock_db, mock_embedding_service):
        """Test summarizing a group of memories"""
        # Setup
        session_id = "test-session"
        
        # Mock memories to be summarized
        mock_memories = [
            {
                'content': 'First memory about the quest.',
                'session_id': session_id,
                'memory_id': 'memory1',
                'memory_type': 'short_term',
                'created_at': datetime.utcnow() - timedelta(hours=2),
                'character_id': 'char1',
                'user_id': 'user1'
            },
            {
                'content': 'Second memory about the artifact.',
                'session_id': session_id,
                'memory_id': 'memory2',
                'memory_type': 'short_term',
                'created_at': datetime.utcnow() - timedelta(hours=1),
                'character_id': 'char1',
                'user_id': 'user1'
            }
        ]
        
        # Set up find query mock with sort and return values
        find_mock = MagicMock()
        sort_mock = MagicMock()
        sort_mock.return_value = mock_memories
        find_mock.sort.return_value = sort_mock
        mock_db.memory_vectors.find.return_value = find_mock
        
        # Mock create_memory_summary from MemoryService
        with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
            mock_memory = MagicMock()
            mock_memory.memory_id = 'summary1'
            mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
            
            # Call the function
            result = summarization_service.summarize_memories(session_id)
            
            # Verify
            assert result['success'] is True
            assert result['summary'].memory_id == 'summary1'
            
            # Verify find was called with the right parameters
            mock_db.memory_vectors.find.assert_called_with({
                'session_id': session_id,
                'memory_type': 'short_term'
            })
            
            # Verify summarize_text was called with combined content
            summarizer_call_arg = summarization_service.summarizer.call_args[0][0]
            assert "Memory 1: First memory" in summarizer_call_arg or "First memory about the quest." in summarizer_call_arg
            assert "Memory 2: Second memory" in summarizer_call_arg or "Second memory about the artifact." in summarizer_call_arg
            
            # Verify embedding service was called
            assert mock_embedding_service.generate_embedding.called
            
            # Verify create_memory_summary was called with correct args
            memory_ids_arg = mock_create_summary.call_args[1].get('memory_ids', [])
            assert 'memory1' in memory_ids_arg
            assert 'memory2' in memory_ids_arg
            
            # Verify memories were marked as summarized
            update_calls = mock_db.memory_vectors.update_one.call_count
            assert update_calls > 0, "No calls to update memories as summarized"

    def test_summarize_memories_no_memories(self, summarization_service, mock_db):
        """Test summarizing when no memories are found"""
        # Setup
        session_id = "test-session"
        
        # Mock empty memory list with proper method chain
        find_mock = MagicMock()
        sort_mock = MagicMock()
        sort_mock.return_value = []  # Empty result
        find_mock.sort.return_value = sort_mock
        mock_db.memory_vectors.find.return_value = find_mock
        
        # Call the function
        result = summarization_service.summarize_memories(session_id)
        
        # Verify
        assert result['success'] is False
        assert 'error' in result
        assert 'No memories found' in result['error'] or 'No memories' in result['error']

    def test_trigger_summarization_if_needed(self, summarization_service):
        """Test automatic triggering of summarization"""
        # Setup
        session_id = "test-session"
        
        # Mock check_summarization_triggers from MemoryService
        with patch('app.services.memory_service_enhanced.EnhancedMemoryService.check_summarization_triggers') as mock_check:
            # First test when summarization is needed
            mock_check.return_value = True
            
            # Also patch summarize_memories to avoid actual summarization
            with patch.object(summarization_service, 'summarize_memories') as mock_summarize:
                mock_summarize.return_value = {'success': True, 'summary': MagicMock()}
                
                # Call the function
                result = summarization_service.trigger_summarization_if_needed(session_id)
                
                # Verify
                assert result['success'] is True
                assert mock_summarize.called
                assert mock_summarize.call_args[0][0] == session_id
                
                # Now test when summarization is not needed
                mock_check.return_value = False
                
                # Reset the mock to check it's not called again
                mock_summarize.reset_mock()
                
                # Call the function again
                result = summarization_service.trigger_summarization_if_needed(session_id)
                
                # Verify
                assert result['success'] is False
                assert 'not needed' in result['message'] or 'Summarization not needed' in result['message']
                assert not mock_summarize.called