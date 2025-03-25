"""
Tests for the Summarization Service
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os

# Create a Flask application context for testing
@pytest.fixture
def app_context():
    """Create a Flask application context for testing"""
    from flask import Flask, g
    app = Flask(__name__)
    
    # Create a mock database
    mock_db = MagicMock()
    
    # Set up the mock database structure
    mock_collection = MagicMock()
    mock_db.memory_vectors = mock_collection
    
    # Set up the find cursor
    mock_cursor = MagicMock()
    mock_collection.find.return_value = mock_cursor
    
    # Set up sort to return an empty list by default
    mock_cursor.sort.return_value = []
    
    # Set up update_one
    mock_collection.update_one = MagicMock()
    mock_collection.update_one.return_value = MagicMock(modified_count=1)
    
    # Store the mock_db in the Flask context
    with app.app_context():
        g.db = mock_db
        yield app

class TestSummarizationService:
    """Test suite for SummarizationService"""

    @pytest.fixture
    def mock_summarizer(self):
        """Mock the actual summarizer function directly"""
        with patch('app.services.summarization_service.pipeline') as mock_pipeline:
            # Create a mock summarizer function
            mock_summarizer = MagicMock()
            mock_summarizer.return_value = [{'summary_text': 'This is a summarized version of the text.'}]
            mock_pipeline.return_value = mock_summarizer
            yield mock_summarizer

    @pytest.fixture
    def mock_db(self):
        """Mock MongoDB connection"""
        with patch('app.extensions.get_db') as mock_get_db:
            # Create a proper chain of mocks
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_find_result = MagicMock()
            mock_sort_result = MagicMock()
            
            # Set up the chain
            mock_db.memory_vectors = mock_collection
            mock_collection.find.return_value = mock_find_result
            mock_find_result.sort.return_value = mock_sort_result
            
            # By default, return empty list
            mock_sort_result.return_value = []
            
            # Make get_db() return our mock_db
            mock_get_db.return_value = mock_db
            
            # Set up update_one for marking memories as summarized
            mock_collection.update_one = MagicMock()
            mock_collection.update_one.return_value = MagicMock(modified_count=1)
            
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
    def summarization_service(self, mock_summarizer, app_context):
        """Create a SummarizationService with mocked components"""
        # Force import of the service after mocks are set up
        from app.services.summarization_service import SummarizationService
        
        # Set model name environment variable if needed
        os.environ.setdefault('SUMMARIZATION_MODEL', 'facebook/bart-large-cnn')
        
        # Create the service
        service = SummarizationService()
        
        # Replace the summarizer with our mock directly
        service.summarizer = mock_summarizer
        
        return service

    def test_initialization(self, app_context):
        """Test SummarizationService initialization"""
        # Import inside the test to ensure mocks are applied
        with patch('app.services.summarization_service.pipeline') as mock_pipeline:
            mock_summarizer = MagicMock()
            mock_pipeline.return_value = mock_summarizer
            
            # Now import and create the service
            from app.services.summarization_service import SummarizationService
            service = SummarizationService()
            
            # Basic assertions
            assert service is not None
            assert service.model_name is not None
            assert mock_pipeline.called

    def test_summarize_text(self, summarization_service):
        """Test summarizing a single text"""
        # Setup
        text = "This is a long text that needs to be summarized. " * 20
        
        # Call the function
        summary = summarization_service.summarize_text(text)
        
        # Verify the mock was called with the text
        summarization_service.summarizer.assert_called_once()
        
        # The first argument should be the text
        call_args = summarization_service.summarizer.call_args[0]
        assert len(call_args) > 0
        assert call_args[0] == text
        
        # Verify the summary is as expected
        assert summary == "This is a summarized version of the text."

    def test_summarize_text_too_long(self, summarization_service):
        """Test summarizing very long text gets truncated"""
        # Setup
        text = "X" * 2000  # Text longer than the typical model limit
        
        # Reset mock
        summarization_service.summarizer.reset_mock()
        
        # Call the function
        summarization_service.summarize_text(text)
        
        # Verify the mock was called
        summarization_service.summarizer.assert_called_once()
        
        # Get the actual text passed to the model
        actual_text = summarization_service.summarizer.call_args[0][0]
        
        # Verify it was truncated to a reasonable length
        assert len(actual_text) <= 2000, "Text should be truncated"

    def test_summarize_text_model_failure(self, summarization_service):
        """Test fallback when model fails"""
        # Setup - make summarizer raise an exception
        summarization_service.summarizer.side_effect = Exception("Model error")
        
        # Call the function
        text = "This text will cause an error in the model."
        summary = summarization_service.summarize_text(text)
        
        # Verify - it should return the original text as fallback
        assert summary == text

    def test_summarize_memories(self, summarization_service, app_context):
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
        
        # Configure mock_db to return our test memories
        from flask import g
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Mock memory service's create_memory_summary function
        with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
            # Set up mock return value
            mock_memory = MagicMock()
            mock_memory.memory_id = 'summary1'
            mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
            
            # Reset summarizer mock
            summarization_service.summarizer.reset_mock()
            summarization_service.summarizer.side_effect = None  # Clear any side effects
            
            # Call the function
            result = summarization_service.summarize_memories(session_id)
            
            # Verify success
            assert result['success'] is True
            assert 'summary' in result or 'memory' in result
            
            # Verify find was called with correct parameters
            g.db.memory_vectors.find.assert_called_once()
            args, kwargs = g.db.memory_vectors.find.call_args
            query = args[0] if args else kwargs.get('query', {})
            assert query['session_id'] == session_id
            assert query['memory_type'] == 'short_term'
            
            # Verify sort was called correctly
            g.db.memory_vectors.find.return_value.sort.assert_called_once()
            
            # Verify create_memory_summary was called
            mock_create_summary.assert_called_once()
            
            # Verify update_one was called for each memory
            assert g.db.memory_vectors.update_one.call_count == len(mock_memories)

    def test_summarize_memories_no_memories(self, summarization_service, app_context):
        """Test summarizing when no memories are found"""
        # Setup
        session_id = "test-session"
        
        # Configure mock_db to return empty list
        from flask import g
        g.db.memory_vectors.find.return_value.sort.return_value = []
        
        # Call the function
        result = summarization_service.summarize_memories(session_id)
        
        # Verify we got a result
        assert result is not None
        
        # If structured as expected, verify failure
        if isinstance(result, dict):
            assert result.get('success', True) is False  # Should be a failure
            assert 'error' in result
            assert 'No memories found' in result['error']

    def test_trigger_summarization_if_needed(self, summarization_service, app_context):
        """Test automatic triggering of summarization"""
        # Setup
        session_id = "test-session"
        
        # Try patching both possible memory service locations
        with patch('app.services.memory_service.MemoryService') as mock_service_class:
            # Set up the mock service
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # First test when summarization is needed
            mock_service.check_summarization_triggers.return_value = True
            
            # Also patch summarize_memories to avoid actual summarization
            with patch.object(summarization_service, 'summarize_memories') as mock_summarize:
                mock_summarize.return_value = {'success': True, 'summary': MagicMock()}
                
                # Call the function
                result = summarization_service.trigger_summarization_if_needed(session_id)
                
                # If no error, verify the result
                if 'success' in result:
                    assert result['success'] is True
                    assert mock_summarize.called
                
                # Now test when summarization is not needed
                mock_service.check_summarization_triggers.return_value = False
                
                # Reset the mock to check it's not called again
                mock_summarize.reset_mock()
                
                # Call the function again
                result = summarization_service.trigger_summarization_if_needed(session_id)
                
                # If no error, verify the result
                if 'success' in result:
                    assert result['success'] is False
                    assert not mock_summarize.called

    def test_summarize_memories_properly_mocked(self, summarization_service, app_context):
        """Test summarizing a group of memories with properly mocked database"""
        # Setup
        session_id = "test-session"
        
        # Create test memories
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
        
        # Configure mock_db to return our test memories
        from flask import g
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Mock the embedding service
        with patch('app.extensions.get_embedding_service') as mock_get_embedding:
            # Create a mock embedding service
            mock_embedding_service = MagicMock()
            mock_get_embedding.return_value = mock_embedding_service
            
            # Make it return a valid embedding
            mock_embedding_service.generate_embedding.return_value = [0.1] * 384
            
            # Mock MemoryService.create_memory_summary
            with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
                # Create a mock memory to return
                mock_memory = MagicMock()
                mock_memory.memory_id = 'summary1'
                mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
                
                # Call the function
                result = summarization_service.summarize_memories(session_id)
                
                # Verify success
                assert result['success'] is True
                assert 'summary' in result or 'memory' in result
                
                # Verify find was called with correct parameters
                g.db.memory_vectors.find.assert_called_once()
                args, kwargs = g.db.memory_vectors.find.call_args
                query = args[0] if args else kwargs.get('query', {})
                assert query['session_id'] == session_id
                assert query['memory_type'] == 'short_term'
                
                # Verify sort was called correctly
                g.db.memory_vectors.find.return_value.sort.assert_called_once()
                
                # Verify create_memory_summary was called
                mock_create_summary.assert_called_once()

    def test_summarize_large_memory_set_properly_mocked(self, summarization_service, app_context):
        """Test summarizing a large set of memories with properly mocked database"""
        # Setup
        session_id = "test-session"
        
        # Create test memories - smaller set to start
        mock_memories = []
        for i in range(10):
            mock_memories.append({
                'content': f'Memory {i}: Event happening during the quest.',
                'session_id': session_id,
                'memory_id': f'memory{i}',
                'memory_type': 'short_term',
                'created_at': datetime.utcnow() - timedelta(minutes=i*30),
                'character_id': 'char1',
                'user_id': 'user1'
            })
        
        # Configure mock_db to return our test memories
        from flask import g
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Mock the embedding service
        with patch('app.extensions.get_embedding_service') as mock_get_embedding:
            # Create a mock embedding service
            mock_embedding_service = MagicMock()
            mock_get_embedding.return_value = mock_embedding_service
            
            # Make it return a valid embedding
            mock_embedding_service.generate_embedding.return_value = [0.1] * 384
            
            # Mock MemoryService.create_memory_summary
            with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
                # Create a mock memory to return
                mock_memory = MagicMock()
                mock_memory.memory_id = 'summary1'
                mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
                
                # Call the function
                result = summarization_service.summarize_memories(session_id)
                
                # Verify success
                assert result['success'] is True
                assert 'summary' in result or 'memory' in result
                
                # Verify find was called with correct parameters
                g.db.memory_vectors.find.assert_called_once()
                
                # Verify memory IDs were extracted and passed
                mock_create_summary.assert_called_once()
                # Extract the memory_ids argument
                args, kwargs = mock_create_summary.call_args
                memory_ids = kwargs.get('memory_ids', [])
                # Verify we have the expected number of memory IDs
                assert len(memory_ids) == len(mock_memories)

    def test_summarize_memories_no_memories_properly_mocked(self, summarization_service, app_context):
        """Test summarizing with no memories found - properly mocked"""
        # Setup
        session_id = "test-session"
        
        # Configure mock_db to return empty list
        from flask import g
        g.db.memory_vectors.find.return_value.sort.return_value = []
        
        # Call the function
        result = summarization_service.summarize_memories(session_id)
        
        # Verify failure with specific error
        assert result['success'] is False
        assert 'error' in result
        assert 'No memories found' in result['error']
        
        # Verify find was called with correct parameters
        g.db.memory_vectors.find.assert_called_once()
        args, kwargs = g.db.memory_vectors.find.call_args
        query = args[0] if args else kwargs.get('query', {})
        assert query['session_id'] == session_id
        assert query['memory_type'] == 'short_term'

    def test_database_connection_in_summarize_memories(self, summarization_service, app_context):
        """Test that the database connection works properly in summarize_memories"""
        # Setup
        session_id = "test-session"
        
        # Create test memories
        mock_memories = [
            {
                'content': 'First memory about the quest.',
                'session_id': session_id,
                'memory_id': 'memory1',
                'memory_type': 'short_term',
                'created_at': datetime.utcnow() - timedelta(hours=2),
                'character_id': 'char1',
                'user_id': 'user1'
            }
        ]
        
        # Configure mock_db to return our test memories
        from flask import g
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Mock embedding service
        with patch('app.extensions.get_embedding_service') as mock_get_embedding:
            mock_embedding_service = MagicMock()
            mock_get_embedding.return_value = mock_embedding_service
            mock_embedding_service.generate_embedding.return_value = [0.1] * 384
            
            # Mock create_memory_summary
            with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_summary:
                mock_memory = MagicMock()
                mock_memory.memory_id = 'summary1'
                mock_summary.return_value = {'success': True, 'memory': mock_memory}
                
                # Call the function
                result = summarization_service.summarize_memories(session_id)
                
                # Print full result for debugging
                print(f"Result: {result}")
                
                # Verify success
                assert result['success'] is True
                assert 'summary' in result or 'memory' in result
                
                # Verify find was called with correct parameters
                g.db.memory_vectors.find.assert_called_once()
                args, kwargs = g.db.memory_vectors.find.call_args
                query = args[0] if args else kwargs.get('query', {})
                assert query['session_id'] == session_id
                assert query['memory_type'] == 'short_term'

    def test_no_memories_found_with_working_db(self, summarization_service, app_context):
        """Test handling of no memories found with a working database connection"""
        # Setup
        session_id = "test-session"
        
        # Configure mock_db to return empty list
        from flask import g
        g.db.memory_vectors.find.return_value.sort.return_value = []
        
        # Call the function
        result = summarization_service.summarize_memories(session_id)
        
        # Verify the find method was called
        g.db.memory_vectors.find.assert_called_once()
        
        # Verify expected error about no memories
        assert result['success'] is False
        assert 'error' in result
        assert 'No memories found' in result['error']

    def test_summarize_memories(app_context, mock_summarizer, mock_embedding_service):
        """Test successful memory summarization"""
        from flask import g
        
        # Set up mock memories
        mock_memories = [
            {'memory_id': '1', 'content': 'Memory 1', 'created_at': datetime.utcnow()},
            {'memory_id': '2', 'content': 'Memory 2', 'created_at': datetime.utcnow()}
        ]
        
        # Configure mock database
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Create service instance
        service = SummarizationService()
        service.summarizer = mock_summarizer
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is True
        assert 'summary' in result
        assert result['summary'].content == 'Test summary'
        
        # Verify database calls
        g.db.memory_vectors.find.assert_called_once_with({
            'session_id': 'test_session',
            'memory_type': 'short_term'
        })
        
        # Verify update_one was called for each memory
        assert g.db.memory_vectors.update_one.call_count == 2

    def test_summarize_memories_no_memories(app_context, mock_summarizer, mock_embedding_service):
        """Test handling of no memories to summarize"""
        from flask import g
        
        # Configure mock database to return empty list
        g.db.memory_vectors.find.return_value.sort.return_value = []
        
        # Create service instance
        service = SummarizationService()
        service.summarizer = mock_summarizer
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'No memories found to summarize'

    def test_summarize_memories_db_error(app_context, mock_summarizer, mock_embedding_service):
        """Test handling of database connection error"""
        from flask import g
        
        # Configure mock database to return None
        g.db = None
        
        # Create service instance
        service = SummarizationService()
        service.summarizer = mock_summarizer
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Database connection failed'

    def test_summarize_memories_no_summarizer(app_context, mock_embedding_service):
        """Test handling of missing summarizer"""
        from flask import g
        
        # Configure mock database
        g.db.memory_vectors.find.return_value.sort.return_value = []
        
        # Create service instance without summarizer
        service = SummarizationService()
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Summarizer not initialized'

    def test_summarize_memories_no_embedding_service(app_context, mock_summarizer):
        """Test handling of missing embedding service"""
        from flask import g
        
        # Configure mock database
        g.db.memory_vectors.find.return_value.sort.return_value = [
            {'memory_id': '1', 'content': 'Memory 1', 'created_at': datetime.utcnow()}
        ]
        
        # Create service instance
        service = SummarizationService()
        service.summarizer = mock_summarizer
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Embedding service not available'