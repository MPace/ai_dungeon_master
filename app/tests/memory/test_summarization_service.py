"""
Tests for the Summarization Service with Hugging Face Inference API
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import os
import requests

# Import the SummarizationService directly
from app.services.summarization_service import SummarizationService

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
    
    # Set up count_documents
    mock_collection.count_documents = MagicMock(return_value=0)
    
    # Store the mock_db in the Flask context
    with app.app_context():
        g.db = mock_db
        yield app

@pytest.fixture
def mock_api_response():
    """Mock responses from the Hugging Face API"""
    with patch('requests.post') as mock_post:
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'summary_text': 'This is a summarized version of the text.'}]
        mock_post.return_value = mock_response
        yield mock_post

@pytest.fixture
def mock_db():
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
        
        # Set up count_documents
        mock_collection.count_documents = MagicMock(return_value=0)
        
        yield mock_db

@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService"""
    with patch('app.extensions.get_embedding_service') as mock_get_service:
        mock_service = MagicMock()
        # Configure the mock to return predictable embeddings
        mock_service.generate_embedding.return_value = [0.1] * 384
        mock_get_service.return_value = mock_service
        yield mock_service

@pytest.fixture
def summarization_service(mock_api_response, app_context):
    """Create a SummarizationService with mocked components"""
    # Set test API credentials 
    os.environ["HF_API_URL"] = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    os.environ["HF_API_TOKEN"] = "test_token"
    
    # Create the service
    service = SummarizationService()
    
    return service

class TestSummarizationService:
    """Test suite for SummarizationService with Hugging Face Inference API"""

    def test_initialization(self):
        """Test SummarizationService initialization"""
        # Test with environment variables
        with patch.dict(os.environ, {
            "HF_API_URL": "https://test-url.com",
            "HF_API_TOKEN": "test-token"
        }):
            service = SummarizationService()
            assert service.api_url == "https://test-url.com"
            assert service.api_token == "test-token"
        
        # Test with explicit parameters
        service = SummarizationService(
            api_url="https://custom-url.com",
            api_token="custom-token"
        )
        assert service.api_url == "https://custom-url.com"
        assert service.api_token == "custom-token"

    def test_summarize_text(self, summarization_service, mock_api_response):
        """Test summarizing a single text"""
        # Setup
        text = "This is a long text that needs to be summarized. " * 20
        
        # Call the function
        summary = summarization_service.summarize_text(text)
        
        # Verify the API was called with the text
        mock_api_response.assert_called_once()
        
        # Verify the summary is as expected
        assert summary == "This is a summarized version of the text."
        
        # Verify API call parameters
        args, kwargs = mock_api_response.call_args
        assert kwargs['headers']['Authorization'] == "Bearer test_token"
        assert kwargs['json']['inputs'] == text

    def test_summarize_text_too_long(self, summarization_service, mock_api_response):
        """Test summarizing very long text gets truncated"""
        # Setup
        text = "X" * 5000  # Text longer than the limit
        
        # Reset mock
        mock_api_response.reset_mock()
        
        # Call the function
        summarization_service.summarize_text(text)
        
        # Verify the API was called
        mock_api_response.assert_called_once()
        
        # Get the actual text passed to the API
        args, kwargs = mock_api_response.call_args
        actual_text = kwargs['json']['inputs']
        
        # Verify it was truncated to the limit
        assert len(actual_text) <= 4000, "Text should be truncated"

    def test_summarize_text_api_error(self, summarization_service, mock_api_response):
        """Test handling API errors"""
        # Setup - make API return an error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_api_response.return_value = mock_response
        
        # Call the function
        text = "This text will cause an API error."
        summary = summarization_service.summarize_text(text)
        
        # Verify - it should return the original text as fallback
        assert summary == text

    def test_summarize_text_exception(self, summarization_service):
        """Test handling exceptions during API call"""
        # Setup - make requests.post raise an exception
        with patch('requests.post', side_effect=Exception("Connection error")):
            # Call the function
            text = "This text will cause a connection error."
            summary = summarization_service.summarize_text(text)
            
            # Verify - it should return the original text as fallback
            assert summary == text

    def test_summarize_memories(self, app_context, mock_api_response, mock_embedding_service):
        """Test successful memory summarization"""
        from flask import g
        
        # Set up mock memories
        mock_memories = [
            {'memory_id': '1', 'content': 'Memory 1', 'created_at': datetime.utcnow()},
            {'memory_id': '2', 'content': 'Memory 2', 'created_at': datetime.utcnow()}
        ]
        
        # Configure mock database
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Create service instance with API credentials
        service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
        
        # Mock MemoryService.create_memory_summary
        with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
            mock_memory = MagicMock()
            mock_memory.memory_id = 'summary1'
            mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
            
            # Test summarization
            result = service.summarize_memories('test_session')
            
            # Verify result
            assert result['success'] is True
            assert 'summary' in result
            assert result['summary'].memory_id == 'summary1'
            
            # Verify database calls
            g.db.memory_vectors.find.assert_called_once_with({
                'session_id': 'test_session',
                'memory_type': 'short_term'
            })
            
            # Verify update_one was called for each memory
            assert g.db.memory_vectors.update_one.call_count == 2
            
            # Verify API call was made
            mock_api_response.assert_called_once()

    def test_summarize_memories_no_memories(self, app_context, mock_api_response):
        """Test handling of no memories to summarize"""
        from flask import g
        
        # Configure mock database to return empty list
        g.db.memory_vectors.find.return_value.sort.return_value = []
        
        # Create service instance with API credentials
        service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'No memories found to summarize'
        
        # Verify API call was NOT made
        mock_api_response.assert_not_called()

    def test_summarize_memories_properly_mocked(self, app_context, mock_api_response, mock_embedding_service):
        """Test summarizing a group of memories with properly mocked database"""
        from flask import g
        
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
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Create service instance with API credentials
        service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
        
        # Mock MemoryService.create_memory_summary
        with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
            mock_memory = MagicMock()
            mock_memory.memory_id = 'summary1'
            mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
            
            # Call the function
            result = service.summarize_memories(session_id)
            
            # Verify success
            assert result['success'] is True
            assert 'summary' in result
            assert result['summary'].memory_id == 'summary1'
            
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
            
            # Verify API call was made with combined texts
            mock_api_response.assert_called_once()
            api_args, api_kwargs = mock_api_response.call_args
            inputs = api_kwargs['json']['inputs']
            assert 'First memory about the quest' in inputs
            assert 'Second memory about the artifact' in inputs

    def test_database_connection_in_summarize_memories(self, app_context, mock_api_response, mock_embedding_service):
        """Test that the database connection works properly in summarize_memories"""
        from flask import g
        
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
        g.db.memory_vectors.find.return_value.sort.return_value = mock_memories
        
        # Create service instance with API credentials
        service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
        
        # Mock MemoryService.create_memory_summary
        with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
            mock_memory = MagicMock()
            mock_memory.memory_id = 'summary1'
            mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
            
            # Call the function
            result = service.summarize_memories(session_id)
            
            # Verify success
            assert result['success'] is True
            assert 'summary' in result
            assert result['summary'].memory_id == 'summary1'
            
            # Verify find was called with correct parameters
            g.db.memory_vectors.find.assert_called_once()
            args, kwargs = g.db.memory_vectors.find.call_args
            query = args[0] if args else kwargs.get('query', {})
            assert query['session_id'] == session_id
            assert query['memory_type'] == 'short_term'

    def test_summarize_memories_db_error(self, app_context, mock_api_response):
        """Test handling of database connection error"""
        from flask import g
        
        # Configure mock database to return None
        g.db = None
        
        # Create service instance with API credentials
        service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Database connection failed'
        
        # Verify API call was NOT made
        mock_api_response.assert_not_called()

    def test_summarize_memories_no_api_url(self, app_context, mock_embedding_service):
        """Test handling of missing API URL"""
        from flask import g
        
        # Configure mock database
        g.db.memory_vectors.find.return_value.sort.return_value = [
            {'memory_id': '1', 'content': 'Memory 1', 'created_at': datetime.utcnow()}
        ]
        
        # Create service instance without API URL
        service = SummarizationService(api_token="test-token")
        service.api_url = None
        
        # Test summarization
        result = service.summarize_memories('test_session')
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Summarization service not properly configured'

    def test_summarize_memories_no_embedding_service(self, app_context, mock_api_response):
        """Test handling of missing embedding service"""
        from flask import g
        
        # Configure mock database
        g.db.memory_vectors.find.return_value.sort.return_value = [
            {'memory_id': '1', 'content': 'Memory 1', 'created_at': datetime.utcnow()}
        ]
        
        # Create service instance
        service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
        
        # Mock get_embedding_service to return None
        with patch('app.extensions.get_embedding_service', return_value=None):
            # Test summarization
            result = service.summarize_memories('test_session')
            
            # Verify result
            assert result['success'] is False
            assert result['error'] == 'Embedding service not available'
            
            # Verify API call WAS made (summarization happens before embedding)
            mock_api_response.assert_called_once()

    def test_trigger_summarization_needed(self, app_context, mock_api_response):
        """Test triggering summarization when needed"""
        from flask import g
        
        # Setup - configure memory count to trigger summarization
        g.db.memory_vectors.count_documents.return_value = 15
        
        # Mock the summarize_memories method
        with patch.object(SummarizationService, 'summarize_memories') as mock_summarize:
            mock_summarize.return_value = {'success': True, 'summary': 'test-summary'}
            
            # Create service instance
            service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
            
            # Call trigger_summarization_if_needed
            result = service.trigger_summarization_if_needed('test-session')
            
            # Verify summarize_memories was called
            mock_summarize.assert_called_once()
            assert result['success'] is True

    def test_trigger_summarization_not_needed(self, app_context, mock_api_response):
        """Test not triggering summarization when not needed"""
        from flask import g
        
        # Setup - configure memory count to NOT trigger summarization
        g.db.memory_vectors.count_documents.return_value = 5
        
        # Create service instance
        service = SummarizationService(api_url="https://test-url.com", api_token="test-token")
        
        # Call trigger_summarization_if_needed
        result = service.trigger_summarization_if_needed('test-session')
        
        # Verify result
        assert result['success'] is False
        assert result['message'] == 'Summarization not needed'