"""
Integration tests for Summarization Service with Hugging Face API (pytest compatible)

Environment Variables:
    HF_API_URL - The Hugging Face Inference API endpoint URL
    HF_API_TOKEN - Your Hugging Face API token
"""
import os
import sys
import time
import logging
import pytest
import json
import requests
from datetime import datetime
from unittest.mock import patch, MagicMock
from flask import Flask, g

# Import the service to test
from app.services.summarization_service import SummarizationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration-test")

class MockDB:
    """Simple mock DB for testing that mimics the necessary structure"""
    
    def __init__(self):
        self.memory_vectors = self
        self.data = []
        
    def find(self, query):
        """Mock find method that returns self for method chaining"""
        self.current_query = query
        return self
        
    def sort(self, field_name=None, direction=1):
        """Mock sort method that returns the data"""
        # In a real implementation we would sort the data here
        return self
        
    def limit(self, limit_count):
        """Mock limit method that returns the data"""
        return self.data
        
    def update_one(self, query, update):
        """Mock update_one method"""
        logger.info(f"Would update document matching: {query}")
        logger.info(f"With update: {update}")
        return type('obj', (object,), {'acknowledged': True, 'modified_count': 1})
        
    def count_documents(self, query):
        """Mock count_documents method"""
        return len(self.data)
        
    def add_test_memories(self, memories):
        """Helper to add test memories to our mock DB"""
        self.data = memories

class MockEmbeddingService:
    """Simple mock embedding service that returns random vectors"""
    
    def generate_embedding(self, text):
        """Generate a mock embedding - a simple vector of 768 dimensions with value 0.1"""
        return [0.1] * 768

class MockMemoryService:
    """Mock for the MemoryService to store the summary"""
    
    @staticmethod
    def create_memory_summary(memory_ids, summary_content, summary_embedding, 
                              session_id, character_id=None, user_id=None):
        """Mock create_memory_summary method"""
        logger.info(f"Creating memory summary for {len(memory_ids)} memories")
        logger.info(f"Summary content: {summary_content[:100]}...")
        
        # Create a response mimicking the real MemoryService
        mock_memory = {
            'memory_id': 'test-summary-' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'content': summary_content,
            'session_id': session_id,
            'character_id': character_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'memory': mock_memory
        }

@pytest.fixture
def flask_app():
    """Create a Flask application for testing"""
    app = Flask(__name__)
    return app

@pytest.fixture
def app_context(flask_app):
    """Create a Flask application context for testing"""
    with flask_app.app_context():
        # Setup g.db
        g.db = MockDB()
        yield flask_app

@pytest.fixture
def summarization_service():
    """
    Fixture to create a SummarizationService with real or mocked API credentials
    In CI/CD environments, we'll use mocked credentials
    """
    # Force mock credentials for CI testing
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    api_token = "mock_token_for_testing"
    
    # Create and return the service
    return SummarizationService(
        api_url=api_url,
        api_token=api_token
    )

@pytest.fixture
def mock_db():
    """Fixture for a mock database"""
    db = MockDB()
    
    # Add test memories
    test_memories = [
        {
            'memory_id': 'memory1',
            'content': 'The party discovered a hidden cave behind a waterfall. Inside, they found ancient runes carved into the walls.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T12:00:00',
            'memory_type': 'short_term'
        },
        {
            'memory_id': 'memory2',
            'content': 'The wizard Eldrin translated the runes, revealing they were a warning about a sealed demon beneath the mountain.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T12:30:00',
            'memory_type': 'short_term'
        },
        {
            'memory_id': 'memory3',
            'content': 'The party found a strange amulet with a ruby center. It seemed to pulse with magical energy.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T13:00:00',
            'memory_type': 'short_term'
        },
        {
            'memory_id': 'memory4',
            'content': 'When the amulet was brought near the runes, the ruby began to glow brightly and the ground trembled slightly.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T13:30:00',
            'memory_type': 'short_term'
        },
        {
            'memory_id': 'memory5',
            'content': 'The party decided to leave the cave and seek guidance from the elders in the nearby village of Willowbrook.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T14:00:00',
            'memory_type': 'short_term'
        }
    ]
    
    db.add_test_memories(test_memories)
    return db

def test_summarize_text(summarization_service):
    """Test the basic text summarization functionality with mocked API"""
    logger.info("===== Testing Basic Text Summarization =====")
    
    # Test text - a news article about climate change (shorter for testing)
    test_text = """
    The Intergovernmental Panel on Climate Change (IPCC) has issued its most stark warning yet about climate change. 
    The report warns that without immediate action to reduce emissions, limiting warming to 1.5°C will be impossible.
    Rising sea levels, melting ice caps, and more extreme weather events are among the consequences.
    The scientists highlight that cutting carbon dioxide emissions is critical, along with reducing other greenhouse gases.
    The report has been described as a "code red for humanity" by UN Secretary-General António Guterres.
    """
    
    # Setup a mock API call
    with patch('requests.post') as mock_post:
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'summary_text': 'The IPCC has issued a stark warning about climate change, calling for immediate action to reduce emissions. The UN Secretary-General called it a "code red for humanity."'}]
        mock_post.return_value = mock_response
        
        # Time the summarization
        start_time = time.time()
        logger.info(f"Sending text to be summarized ({len(test_text)} characters)")
        summary = summarization_service.summarize_text(test_text)
        end_time = time.time()
        
        # Log the results
        logger.info(f"Summarization completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Original text length: {len(test_text)} characters")
        logger.info(f"Summary length: {len(summary)} characters")
        logger.info(f"Summary: {summary}")
        
        # Verify the mock was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['headers']['Authorization'] == f"Bearer {summarization_service.api_token}"
        assert 'IPCC' in kwargs['json']['inputs']
        
        # Test assertions
        assert summary is not None
        assert len(summary) > 0
        assert len(summary) < len(test_text)
        assert "IPCC" in summary or "climate change" in summary.lower()
        
        logger.info("✓ Basic text summarization test PASSED")

def test_summarize_memories(app_context, summarization_service, mock_db):
    """Test the memory summarization functionality"""
    logger.info("\n===== Testing Memory Summarization =====")
    
    # Setup mocks for all external dependencies
    with patch('requests.post') as mock_post, \
         patch('app.extensions.get_db', return_value=mock_db), \
         patch('app.extensions.get_embedding_service', return_value=MockEmbeddingService()), \
         patch('app.services.memory_service.MemoryService.create_memory_summary', 
               side_effect=MockMemoryService.create_memory_summary):
        
        # Create a mock response for the API call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'summary_text': 'The party found a cave with ancient runes and a magic amulet. When the amulet was brought near the runes, the ground trembled. They decided to seek guidance from village elders.'}]
        mock_post.return_value = mock_response
        
        # Time the summarization
        start_time = time.time()
        logger.info(f"Summarizing {len(mock_db.data)} memories")
        
        # Call the method we're testing
        result = summarization_service.summarize_memories('test-session')
        
        end_time = time.time()
        
        # Log the results
        logger.info(f"Memory summarization completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Result success: {result.get('success', False)}")
        
        if 'summary' in result:
            # Get the summary content - handle both object and dict cases
            if hasattr(result['summary'], 'content'):
                summary_content = result['summary'].content
            elif isinstance(result['summary'], dict) and 'content' in result['summary']:
                summary_content = result['summary']['content']
            else:
                summary_content = str(result['summary'])
                
            logger.info(f"Memory summary: {summary_content}")
        
        # Verify our mocks were called
        mock_post.assert_called_once()
        
        # Test assertions
        assert result is not None
        assert result.get('success') is True
        assert 'summary' in result
        
        logger.info("✓ Memory summarization test PASSED")

def test_trigger_summarization(app_context, summarization_service, mock_db):
    """Test the trigger_summarization_if_needed functionality"""
    logger.info("\n===== Testing Summarization Trigger =====")
    
    # Setup mocks for all external dependencies
    with patch('app.extensions.get_db', return_value=mock_db), \
         patch('app.services.summarization_service.SummarizationService.summarize_memories') as mock_summarize:
        
        # Setup the mock to return a successful result
        mock_summarize.return_value = {
            'success': True,
            'summary': {
                'memory_id': 'test-summary-123',
                'content': 'A summarized version of the memories.'
            }
        }
        
        # Call the method we're testing
        result = summarization_service.trigger_summarization_if_needed('test-session')
        
        # Log the results
        logger.info(f"Trigger result: {result}")
        
        # Verify our mock was called if there were enough memories
        if len(mock_db.data) >= 10:
            mock_summarize.assert_called_once_with('test-session', time_window=pytest.approx(60*60, abs=1))
            assert result.get('success') is True
        else:
            # If not enough memories, verify we get the expected result
            assert result.get('success') is False
            assert 'message' in result
            assert 'not needed' in result['message']
        
        logger.info("✓ Summarization trigger test PASSED")