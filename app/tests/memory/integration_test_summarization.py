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
        self.current_query = {}
        
    def find(self, query):
        """Mock find method that returns self for method chaining"""
        self.current_query = query
        return self
        
    def sort(self, field_name=None, direction=1):
        """Mock sort method that returns self for method chaining"""
        # In a real implementation we would sort the data here
        return self
        
    def limit(self, limit_count):
        """Mock limit method that returns the filtered data"""
        # Filter data based on current_query
        filtered_data = []
        for memory in self.data:
            # Handle session_id filter
            if 'session_id' in self.current_query and memory.get('session_id') != self.current_query['session_id']:
                continue
            
            # Handle memory_type filter
            if 'memory_type' in self.current_query and memory.get('memory_type') != self.current_query['memory_type']:
                continue
                
            filtered_data.append(memory)
            
        return filtered_data
        
    def __iter__(self):
        """Make the object iterable, returning filtered data based on current query"""
        # Return iterator for filtered data based on the current query
        filtered_data = []
        for memory in self.data:
            # Handle session_id filter
            if 'session_id' in self.current_query and memory.get('session_id') != self.current_query['session_id']:
                continue
            
            # Handle memory_type filter
            if 'memory_type' in self.current_query and memory.get('memory_type') != self.current_query['memory_type']:
                continue
                
            filtered_data.append(memory)
            
        return iter(filtered_data)
        
    def update_one(self, query, update):
        """Mock update_one method"""
        logger.info(f"Would update document matching: {query}")
        logger.info(f"With update: {update}")
        return type('obj', (object,), {'acknowledged': True, 'modified_count': 1})
        
    def count_documents(self, query):
        """Mock count_documents method"""
        # Count documents matching the query
        count = 0
        for memory in self.data:
            matches = True
            for key, value in query.items():
                # Handle special operators
                if isinstance(value, dict) and '$in' in value:
                    if key not in memory or memory[key] not in value['$in']:
                        matches = False
                        break
                elif isinstance(value, dict) and '$ne' in value:
                    if key in memory and memory[key] == value['$ne']:
                        matches = False
                        break
                elif isinstance(value, dict) and '$exists' in value:
                    exists = key in memory
                    if exists != value['$exists']:
                        matches = False
                        break
                else:
                    # Simple equality check
                    if key not in memory or memory[key] != value:
                        matches = False
                        break
            
            if matches:
                count += 1
                
        return count
        
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
    
    expected_summary = 'The IPCC has issued a stark warning about climate change, calling for immediate action to reduce emissions. The UN Secretary-General called it a "code red for humanity."'
    
    # Setup our mock
    with patch('requests.post') as mock_post:
        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'summary_text': expected_summary}]
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
        
        # Check the API call parameters
        args, kwargs = mock_post.call_args
        assert 'headers' in kwargs
        assert 'Authorization' in kwargs['headers']
        assert 'json' in kwargs
        assert 'inputs' in kwargs['json']
        assert test_text.strip() in kwargs['json']['inputs']
        
        # Test assertions on the result
        assert summary == expected_summary
        assert len(summary) > 0
        assert len(summary) < len(test_text)
        
        logger.info("✓ Basic text summarization test PASSED")

def test_summarize_memories(app_context, summarization_service, mock_db):
    """Test the memory summarization functionality"""
    logger.info("\n===== Testing Memory Summarization =====")
    
    # Direct patching of the summarize_text method to avoid API calls
    with patch.object(summarization_service, 'summarize_text') as mock_summarize_text, \
         patch('app.extensions.get_db', return_value=mock_db), \
         patch('app.extensions.get_embedding_service', return_value=MockEmbeddingService()), \
         patch('app.services.memory_service.MemoryService.create_memory_summary', 
               side_effect=MockMemoryService.create_memory_summary):
        
        # Set up the mock summarize_text to return a fixed response
        mock_summarize_text.return_value = 'The party found a cave with ancient runes and a magic amulet. When the amulet was brought near the runes, the ground trembled. They decided to seek guidance from village elders.'
        
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
        
        # Verify our summarize_text mock was called at least once
        mock_summarize_text.assert_called_once()
        
        # Test assertions
        assert result is not None
        assert result.get('success') is True
        assert 'summary' in result
        
        logger.info("✓ Memory summarization test PASSED")

def test_trigger_summarization(app_context, summarization_service, mock_db):
    """Test the trigger_summarization_if_needed functionality"""
    logger.info("\n===== Testing Summarization Trigger =====")
    
    # Add more test memories to trigger summarization (need at least 10)
    additional_memories = []
    for i in range(6, 11):  # We already have 5, add 5 more
        additional_memories.append({
            'memory_id': f'memory{i}',
            'content': f'Additional test memory {i}',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': f'2023-01-01T15:0{i-6}:00',
            'memory_type': 'short_term'
        })
    
    # Copy the existing data and add new memories
    all_memories = mock_db.data.copy()
    all_memories.extend(additional_memories)
    
    # Create a separate mock_db with more memories
    large_mock_db = MockDB()
    large_mock_db.add_test_memories(all_memories)
    
    # Test case 1: Not enough memories (using original mock_db)
    logger.info("Test Case 1: Not enough memories")
    with patch('app.extensions.get_db', return_value=mock_db):
        # Call the method we're testing with not enough memories
        result = summarization_service.trigger_summarization_if_needed('test-session')
        
        # Log the results
        logger.info(f"Trigger result (not enough memories): {result}")
        
        # Verify we get the expected result when not enough memories
        assert result.get('success') is False
        assert 'message' in result
        assert 'not needed' in result['message']
    
    # Test case 2: Enough memories to trigger summarization
    logger.info("Test Case 2: Enough memories to trigger summarization")
    with patch('app.extensions.get_db', return_value=large_mock_db), \
         patch.object(summarization_service, 'summarize_memories') as mock_summarize:
        
        # Setup the mock to return a successful result
        mock_summarize.return_value = {
            'success': True,
            'summary': {
                'memory_id': 'test-summary-123',
                'content': 'A summarized version of the memories.'
            }
        }
        
        # Call the method we're testing with enough memories
        result = summarization_service.trigger_summarization_if_needed('test-session')
        
        # Log the results
        logger.info(f"Trigger result (enough memories): {result}")
        
        # Verify our summarize_memories mock was called
        from datetime import timedelta
        mock_summarize.assert_called_once()
        args, kwargs = mock_summarize.call_args
        assert args[0] == 'test-session'
        assert isinstance(kwargs.get('time_window'), timedelta)
        
        # Verify success result
        assert result.get('success') is True
            
    logger.info("✓ Summarization trigger test PASSED")