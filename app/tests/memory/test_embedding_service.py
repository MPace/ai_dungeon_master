"""
Tests for the Embedding Service
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.services.embedding_service import EmbeddingService

class TestEmbeddingService:
    """Test suite for EmbeddingService"""

    @pytest.fixture
    def mock_model(self):
        """Mock AutoModel from Hugging Face"""
        with patch('transformers.AutoModel.from_pretrained') as mock_model:
            # Configure the mock model to return predictable outputs
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            
            # Configure the mock hidden state output for mean pooling
            mock_last_hidden_state = MagicMock()
            mock_outputs = MagicMock()
            mock_outputs.last_hidden_state = mock_last_hidden_state
            mock_instance.return_value = mock_outputs
            
            yield mock_model

    @pytest.fixture
    def mock_tokenizer(self):
        """Mock AutoTokenizer from Hugging Face"""
        with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
            # Configure the mock tokenizer
            mock_instance = MagicMock()
            mock_tokenizer.return_value = mock_instance
            
            # Make tokenizer return a simple tensor with attention mask
            def mock_tokenize(text, return_tensors=None, padding=None, truncation=None, max_length=None):
                import torch
                # Create a simple mock tensor that matches what the real tokenizer would return
                return {
                    'input_ids': torch.ones((1, 10), dtype=torch.long),
                    'attention_mask': torch.ones((1, 10), dtype=torch.long)
                }
            
            mock_instance.side_effect = mock_tokenize
            yield mock_tokenizer

    @pytest.fixture
    def embedding_service(self, mock_model, mock_tokenizer):
        """Create an EmbeddingService with mocked dependencies"""
        # Mock torch.cuda.is_available to always return False for testing
        with patch('torch.cuda.is_available', return_value=False):
            service = EmbeddingService(model_name="test-model")
            # Mock the model forward pass to return predictable embeddings
            def mock_forward(*args, **kwargs):
                import torch
                # Return a tensor with a shape that matches what the model would output
                last_hidden_state = torch.ones((1, 10, 384), dtype=torch.float)
                return type('MockOutput', (), {'last_hidden_state': last_hidden_state})()

                
            
            service.model.forward = mock_forward
            service.model.__call__ = mock_forward
            return service

    def test_initialization(self, embedding_service):
        """Test that EmbeddingService initializes correctly"""
        assert embedding_service is not None
        assert embedding_service.model_name == "test-model"
        assert embedding_service.embedding_dim == 384  # Default for all-MiniLM-L6-v2
    
    def test_generate_embedding(self, embedding_service):
        """Test generating an embedding from text"""
        # Configuration specific to this test
        with patch.object(embedding_service.model, '__call__') as mock_call:
            import torch
            # Mock the model's forward pass to return a fixed tensor
            last_hidden_state = torch.ones((1, 10, 384), dtype=torch.float)
            
            class MockOutput:
                def __init__(self, hidden_state):
                    self.last_hidden_state = hidden_state
            
            mock_call.return_value = MockOutput(last_hidden_state)
            
            # Call the function
            embedding = embedding_service.generate_embedding("This is a test text")
            
            # Verify the output
            assert isinstance(embedding, list)
            assert len(embedding) == 384  # Check dimension
            assert all(isinstance(x, float) for x in embedding)  # Check types
    
    def test_embedding_caching(self, embedding_service):
        """Test that embeddings are cached and reused"""
        test_text = "This is a test for caching"
        
        # Configure mock forward pass
        with patch.object(embedding_service.model, '__call__') as mock_call:
            import torch
            # Return a tensor with recognizable values
            values = torch.ones((1, 10, 384), dtype=torch.float) * 0.5
            
            class MockOutput:
                def __init__(self, hidden_state):
                    self.last_hidden_state = hidden_state
            
            mock_call.return_value = MockOutput(values)
            
            # First call should compute the embedding
            first_embedding = embedding_service.generate_embedding(test_text)
            
            # Second call should use the cache
            second_embedding = embedding_service.generate_embedding(test_text)
            
            # Both should be identical
            assert first_embedding == second_embedding
            
            # Model should only be called once
            assert mock_call.call_count == 1
            
            # Check cache stats
            cache_stats = embedding_service.get_cache_stats()
            assert cache_stats['cache_hits'] == 1
            assert cache_stats['cache_misses'] == 1
    
    def test_generate_batch_embeddings(self, embedding_service):
        """Test generating embeddings for a batch of texts"""
        texts = ["First test text", "Second test text", "Third test text"]
        
        # Configure mock forward pass
        with patch.object(embedding_service.model, '__call__') as mock_call:
            import torch
            # Return a tensor with shape matching batch size
            values = torch.ones((3, 10, 384), dtype=torch.float) * 0.5
            
            class MockOutput:
                def __init__(self, hidden_state):
                    self.last_hidden_state = hidden_state
            
            mock_call.return_value = MockOutput(values)
            
            # Generate batch embeddings
            embeddings = embedding_service.generate_batch_embeddings(texts)
            
            # Check results
            assert len(embeddings) == 3
            assert all(len(emb) == 384 for emb in embeddings)
            
            # Model should be called once for the batch
            assert mock_call.call_count == 1
    
    def test_fallback_behavior(self, embedding_service):
        """Test fallback behavior when model fails"""
        # Make the model raise an exception
        with patch.object(embedding_service.model, '__call__', side_effect=Exception("Model error")):
            # It should return a zero vector without failing
            embedding = embedding_service.generate_embedding("This should cause an error")
            
            # Check that we got a zero vector of the correct size
            assert len(embedding) == 384
            assert all(x == 0.0 for x in embedding)