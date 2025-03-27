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
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the service to test
from app.services.summarization_service import SummarizationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration-test")

# Skip these tests if no API credentials are provided
pytestmark = [
    pytest.mark.skipif(
        not os.environ.get("HF_API_URL") or not os.environ.get("HF_API_TOKEN"),
        reason="Missing HF_API_URL or HF_API_TOKEN environment variables"
    )
]

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
        return self.data
        
    def update_one(self, query, update):
        """Mock update_one method"""
        logger.info(f"Would update document matching: {query}")
        logger.info(f"With update: {update}")
        return type('obj', (object,), {'modified_count': 1})
        
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
def summarization_service():
    """Fixture to create a SummarizationService with real API credentials"""
    api_url = os.environ.get("HF_API_URL")
    api_token = os.environ.get("HF_API_TOKEN")
    
    if not api_url or not api_token:
        pytest.skip("HF_API_URL or HF_API_TOKEN environment variables not set")
    
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
            'created_at': '2023-01-01T12:00:00'
        },
        {
            'memory_id': 'memory2',
            'content': 'The wizard Eldrin translated the runes, revealing they were a warning about a sealed demon beneath the mountain.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T12:30:00'
        },
        {
            'memory_id': 'memory3',
            'content': 'The party found a strange amulet with a ruby center. It seemed to pulse with magical energy.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T13:00:00'
        },
        {
            'memory_id': 'memory4',
            'content': 'When the amulet was brought near the runes, the ruby began to glow brightly and the ground trembled slightly.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T13:30:00'
        },
        {
            'memory_id': 'memory5',
            'content': 'The party decided to leave the cave and seek guidance from the elders in the nearby village of Willowbrook.',
            'session_id': 'test-session',
            'character_id': 'character1',
            'user_id': 'user1',
            'created_at': '2023-01-01T14:00:00'
        }
    ]
    
    db.add_test_memories(test_memories)
    return db

def test_summarize_text(summarization_service):
    """Test the basic text summarization functionality"""
    # Skip if no API credentials
    if not summarization_service.api_url or not summarization_service.api_token:
        pytest.skip("API credentials not configured")
    
    logger.info("===== Testing Basic Text Summarization =====")
    
    # Test text - a news article about climate change
    test_text = """
    The Intergovernmental Panel on Climate Change (IPCC) has issued its most stark warning yet about the impact of human activities on the planet. The report, compiled by more than 200 scientists from over 60 countries, warns that without immediate, rapid, and large-scale reductions in greenhouse gas emissions, limiting warming to 1.5°C or even 2°C will be beyond reach. The report emphasizes that climate change is already affecting every region on Earth, with some changes now irreversible. Rising sea levels, melting ice caps, and more frequent extreme weather events like floods, heatwaves, and droughts are among the consequences. The scientists highlight that cutting carbon dioxide emissions is the most important action, but reducing other greenhouse gases like methane would also have significant benefits. The report has been described as a "code red for humanity" by UN Secretary-General António Guterres, who called for immediate action from governments, businesses, and individuals to prevent climate catastrophe.
    """
    
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
    
    # Test assertions
    assert summary is not None
    assert len(summary) > 0
    assert len(summary) < len(test_text)
    assert summary != test_text
    
    logger.info("✓ Basic text summarization test PASSED")

def test_summarize_memories(summarization_service, mock_db):
    """Test the memory summarization functionality"""
    # Skip if no API credentials
    if not summarization_service.api_url or not summarization_service.api_token:
        pytest.skip("API credentials not configured")
    
    logger.info("\n===== Testing Memory Summarization =====")
    
    # Setup mocks for database and services
    with patch('app.extensions.get_db', return_value=mock_db), \
         patch('app.extensions.get_embedding_service', return_value=MockEmbeddingService()), \
         patch('app.services.memory_service.MemoryService.create_memory_summary', 
               side_effect=MockMemoryService.create_memory_summary):
        
        # Time the summarization
        start_time = time.time()
        logger.info(f"Summarizing {len(mock_db.data)} memories")
        
        # Call the method we're testing
        result = summarization_service.summarize_memories('test-session')
        
        end_time = time.time()
        
        # Log the results
        logger.info(f"Memory summarization completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Result success: {result.get('success')}")
        
        if 'summary' in result:
            # Get the summary content
            if hasattr(result['summary'], 'content'):
                summary_content = result['summary'].content
            elif isinstance(result['summary'], dict) and 'content' in result['summary']:
                summary_content = result['summary']['content']
            else:
                summary_content = str(result['summary'])
                
            logger.info(f"Memory summary: {summary_content}")
        
        # Test assertions
        assert result is not None
        assert result.get('success') is True
        assert 'summary' in result
        
        logger.info("✓ Memory summarization test PASSED")