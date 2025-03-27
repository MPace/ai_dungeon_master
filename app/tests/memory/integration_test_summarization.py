#!/usr/bin/env python3
"""
Integration Test for Summarization Service with Hugging Face API

This script performs real API calls to the Hugging Face Inference API
to verify that the summarization service works end-to-end.

Usage:
    HF_API_URL="your_api_endpoint" HF_API_TOKEN="your_api_token" python integration_test_summarization.py

Environment Variables:
    HF_API_URL - The Hugging Face Inference API endpoint URL
    HF_API_TOKEN - Your Hugging Face API token
"""
import os
import sys
import time
import json
import logging
from datetime import datetime
import requests
from pprint import pformat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("integration-test")

# Import the SummarizationService - adjust the import path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from app.services.summarization_service import SummarizationService
    logger.info("Successfully imported SummarizationService")
except ImportError as e:
    logger.error(f"Failed to import SummarizationService: {e}")
    logger.error("Make sure the PYTHONPATH is set correctly")
    sys.exit(1)

class MockDB:
    """Simple mock DB for testing that mimics the necessary structure"""
    
    def __init__(self):
        self.memory_vectors = self
        self.data = []
        
    def find(self, query):
        """Mock find method that returns self for method chaining"""
        self.current_query = query
        return self
        
    def sort(self, field_name, direction=1):
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

def get_api_credentials():
    """Get the Hugging Face API credentials from environment variables"""
    api_url = os.environ.get("HF_API_URL")
    api_token = os.environ.get("HF_API_TOKEN")
    
    if not api_url:
        logger.error("HF_API_URL environment variable not set")
        logger.error("Please set it to your Hugging Face Inference API endpoint URL")
        logger.error("Example: HF_API_URL=https://api-inference.huggingface.co/models/facebook/bart-large-cnn")
        sys.exit(1)
        
    if not api_token:
        logger.error("HF_API_TOKEN environment variable not set")
        logger.error("Please set it to your Hugging Face API token")
        logger.error("You can get a token from https://huggingface.co/settings/tokens")
        sys.exit(1)
        
    return api_url, api_token

def test_summarize_text(service):
    """Test the basic text summarization functionality"""
    logger.info("===== Testing Basic Text Summarization =====")
    
    # Test text - a news article about climate change
    test_text = """
    The Intergovernmental Panel on Climate Change (IPCC) has issued its most stark warning yet about the impact of human activities on the planet. The report, compiled by more than 200 scientists from over 60 countries, warns that without immediate, rapid, and large-scale reductions in greenhouse gas emissions, limiting warming to 1.5°C or even 2°C will be beyond reach. The report emphasizes that climate change is already affecting every region on Earth, with some changes now irreversible. Rising sea levels, melting ice caps, and more frequent extreme weather events like floods, heatwaves, and droughts are among the consequences. The scientists highlight that cutting carbon dioxide emissions is the most important action, but reducing other greenhouse gases like methane would also have significant benefits. The report has been described as a "code red for humanity" by UN Secretary-General António Guterres, who called for immediate action from governments, businesses, and individuals to prevent climate catastrophe.
    """
    
    # Time the summarization
    start_time = time.time()
    logger.info(f"Sending text to be summarized ({len(test_text)} characters)")
    summary = service.summarize_text(test_text)
    end_time = time.time()
    
    # Log the results
    logger.info(f"Summarization completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Original text length: {len(test_text)} characters")
    logger.info(f"Summary length: {len(summary)} characters")
    logger.info(f"Summary: {summary}")
    
    # Check if the summarization worked
    if summary and summary != test_text:
        logger.info("✓ Basic text summarization test PASSED")
    else:
        logger.error("✗ Basic text summarization test FAILED")
        logger.error("The summary is empty or identical to the input text")
    
    return summary

def test_summarize_memories(service):
    """Test the memory summarization functionality"""
    logger.info("\n===== Testing Memory Summarization =====")
    
    # Create test memories
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
    
    # Create a mock DB and add the test memories
    mock_db = MockDB()
    mock_db.add_test_memories(test_memories)
    
    # Mock the DB and embedding service
    with patch_get_db(mock_db), patch_get_embedding_service(MockEmbeddingService()), \
         patch_memory_service():
        
        # Time the summarization
        start_time = time.time()
        logger.info(f"Summarizing {len(test_memories)} memories")
        
        # Call the method we're testing
        result = service.summarize_memories('test-session')
        
        end_time = time.time()
        
        # Log the results
        logger.info(f"Memory summarization completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Result: {pformat(result)}")
        
        # Check if the summarization worked
        if result and result.get('success') and 'summary' in result:
            logger.info("✓ Memory summarization test PASSED")
            
            # Get the summary content
            if hasattr(result['summary'], 'content'):
                summary_content = result['summary'].content
            elif isinstance(result['summary'], dict) and 'content' in result['summary']:
                summary_content = result['summary']['content']
            else:
                summary_content = "Summary content not found in result"
                
            logger.info(f"Memory summary: {summary_content}")
        else:
            logger.error("✗ Memory summarization test FAILED")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
    
    return result

# Context managers for patching
class patch_get_db:
    """Context manager to patch get_db"""
    def __init__(self, mock_db):
        self.mock_db = mock_db
        self.original_get_db = None
        
    def __enter__(self):
        # Save the original function
        from app.extensions import get_db as original_get_db
        self.original_get_db = original_get_db
        
        # Replace with our mock
        import app.extensions
        app.extensions.get_db = lambda: self.mock_db
        return self.mock_db
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore the original function
        import app.extensions
        app.extensions.get_db = self.original_get_db

class patch_get_embedding_service:
    """Context manager to patch get_embedding_service"""
    def __init__(self, mock_service):
        self.mock_service = mock_service
        self.original_get_embedding_service = None
        
    def __enter__(self):
        # Save the original function
        from app.extensions import get_embedding_service as original_get_embedding_service
        self.original_get_embedding_service = original_get_embedding_service
        
        # Replace with our mock
        import app.extensions
        app.extensions.get_embedding_service = lambda: self.mock_service
        return self.mock_service
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore the original function
        import app.extensions
        app.extensions.get_embedding_service = self.original_get_embedding_service

class patch_memory_service:
    """Context manager to patch MemoryService.create_memory_summary"""
    def __enter__(self):
        # Save the original function
        from app.services.memory_service import MemoryService
        self.original_create_memory_summary = MemoryService.create_memory_summary
        
        # Replace with our mock
        MemoryService.create_memory_summary = MockMemoryService.create_memory_summary
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore the original function
        from app.services.memory_service import MemoryService
        MemoryService.create_memory_summary = self.original_create_memory_summary

def main():
    """Main entry point for the integration test"""
    logger.info("Starting Summarization Service Integration Test")
    
    # Get API credentials
    api_url, api_token = get_api_credentials()
    logger.info(f"Using API URL: {api_url}")
    logger.info(f"Using API token: {api_token[:4]}...{api_token[-4:]}")
    
    try:
        # Create the summarization service
        service = SummarizationService(api_url=api_url, api_token=api_token)
        logger.info("Successfully created SummarizationService")
        
        # Test basic text summarization
        summary = test_summarize_text(service)
        
        # Test memory summarization
        result = test_summarize_memories(service)
        
        logger.info("\n===== Integration Test Summary =====")
        if summary and summary != "" and result and result.get('success'):
            logger.info("✓ All tests PASSED")
            return 0
        else:
            logger.error("✗ Some tests FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"Integration test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())