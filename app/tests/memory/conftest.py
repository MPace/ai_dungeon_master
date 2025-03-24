"""
Pytest configuration for testing the AI Dungeon Master
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the application directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        "MONGO_URI": "mongodb://localhost:27017/aidm_test",
        "AI_API_KEY": "fake-test-api-key",
        "AI_MODEL": "grok-2-test",
        "FLASK_ENV": "testing"
    }):
        yield

@pytest.fixture(scope="session", autouse=True)
def prevent_external_requests():
    """Prevent tests from making external HTTP requests"""
    with patch("requests.get"), patch("requests.post"), patch("requests.put"), patch("requests.delete"):
        yield

@pytest.fixture
def mock_flask_app():
    """Create a mock Flask app for testing"""
    with patch("flask.current_app") as mock_app:
        # Configure the mock app
        mock_app.config = {
            "AI_API_KEY": "fake-test-api-key",
            "AI_MODEL": "grok-2-test",
            "MONGO_URI": "mongodb://localhost:27017/aidm_test",
            "TESTING": True
        }
        yield mock_app

@pytest.fixture
def mock_torch():
    """Mock PyTorch to avoid GPU-related issues in testing"""
    with patch("torch.cuda.is_available", return_value=False), \
         patch("torch.device", return_value="cpu"):
        yield

@pytest.fixture
def mock_transformers():
    """Mock Hugging Face transformers to avoid loading models"""
    with patch("transformers.AutoModel.from_pretrained") as mock_model, \
         patch("transformers.AutoTokenizer.from_pretrained") as mock_tokenizer, \
         patch("transformers.pipeline") as mock_pipeline:
        
        # Configure mock model
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance
        
        # Configure mock tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance
        
        # Configure mock pipeline
        mock_pipeline_instance = MagicMock()
        mock_pipeline.return_value = mock_pipeline_instance
        
        yield mock_model, mock_tokenizer, mock_pipeline