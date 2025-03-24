"""
Tests for the Embedding Service
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import torch
from app.services.embedding_service import EmbeddingService

class TestEmbeddingService:
    """Test suite for EmbeddingService"""

    @pytest.fixture
    def mock_model(self):
        """Mock AutoModel from Hugging Face"""
        with patch('transformers.AutoModel.from_pretrained') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            mock_instance.eval = MagicMock(return_value=mock_instance)
            mock_instance.to = MagicMock(return_value=mock_instance)
            
            # Set up the forward pass
            def mock_forward(**kwargs):
                batch_size = kwargs['input_ids'].shape[0]
                return type('MockOutput', (), {
                    'last_hidden_state': torch.ones((batch_size, 10, 384), dtype=torch.float) * 0.5
                })()
            
            mock_instance.forward = mock_forward
            mock_instance.__call__ = mock_forward
            
            yield mock_instance

    @pytest.fixture
    def mock_tokenizer(self):
        """Mock AutoTokenizer from Hugging Face"""
        with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
            def mock_tokenize(texts, **kwargs):
                if isinstance(texts, str):
                    batch_size = 1
                else:
                    batch_size = len(texts)
                
                return {
                    'input_ids': torch.ones((batch_size, 10), dtype=torch.long),
                    'attention_mask': torch.ones((batch_size, 10), dtype=torch.long)
                }
            
            mock_instance = MagicMock()
            mock_instance.__call__ = mock_tokenize
            mock_instance.side_effect = mock_tokenize
            mock_tokenizer.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def embedding_service(self):
        """Create an EmbeddingService with mocked dependencies"""
        with patch('torch.cuda.is_available', return_value=False), \
             patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('transformers.AutoModel.from_pretrained') as mock_model:
            
            # Set up tokenizer mock
            def mock_tokenize(texts, **kwargs):
                if isinstance(texts, str):
                    batch_size = 1
                else:
                    batch_size = len(texts)
                return {
                    'input_ids': torch.ones((batch_size, 10), dtype=torch.long),
                    'attention_mask': torch.ones((batch_size, 10), dtype=torch.long)
                }
            
            tokenizer_instance = MagicMock()
            tokenizer_instance.__call__ = mock_tokenize
            mock_tokenizer.return_value = tokenizer_instance
            
            # Set up model mock
            model_instance = MagicMock()
            def mock_forward(**kwargs):
                batch_size = kwargs['input_ids'].shape[0]
                return type('MockOutput', (), {
                    'last_hidden_state': torch.ones((batch_size, 10, 384), dtype=torch.float) * 0.5
                })()
            
            model_instance.forward = mock_forward
            model_instance.__call__ = mock_forward
            model_instance.eval = MagicMock(return_value=model_instance)
            model_instance.to = MagicMock(return_value=model_instance)
            mock_model.return_value = model_instance
            
            service = EmbeddingService(model_name="test-model")
            return service

    def test_initialization(self, embedding_service):
        """Test that EmbeddingService initializes correctly"""
        assert embedding_service is not None
        assert embedding_service.model_name == "test-model"
        assert embedding_service.embedding_dim == 384

    def test_generate_embedding(self, embedding_service):
        """Test generating an embedding from text"""
        # Call the function
        embedding = embedding_service.generate_embedding("This is a test text")
        
        # Verify the output
        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        assert not all(x == 0.0 for x in embedding)  # Make sure we're not getting zero vectors

    def test_embedding_caching(self, embedding_service):
        """Test that embeddings are cached and reused"""
        test_text = "This is a test for caching"
        
        # First call should compute the embedding
        first_embedding = embedding_service.generate_embedding(test_text)
        
        # Verify first embedding is valid
        assert len(first_embedding) == 384
        assert not all(x == 0.0 for x in first_embedding)
        
        # Second call should use the cache
        second_embedding = embedding_service.generate_embedding(test_text)
        
        # Both should be identical
        assert first_embedding == second_embedding
        
        # Check cache stats
        cache_stats = embedding_service.get_cache_stats()
        assert cache_stats['cache_hits'] == 1
        assert cache_stats['cache_misses'] == 1

    def test_generate_batch_embeddings(self, embedding_service):
        """Test generating embeddings for a batch of texts"""
        texts = ["First test text", "Second test text", "Third test text"]
        
        # Generate batch embeddings
        embeddings = embedding_service.generate_batch_embeddings(texts)
        
        # Check results
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)
        assert all(not all(x == 0.0 for x in emb) for emb in embeddings)  # No zero vectors

    def test_fallback_behavior(self, embedding_service):
        """Test fallback behavior when model fails"""
        with patch.object(embedding_service.model, '__call__', side_effect=Exception("Model error")):
            # It should return a zero vector without failing
            embedding = embedding_service.generate_embedding("This should cause an error")
            
            # Check that we got a zero vector of the correct size
            assert len(embedding) == 384
            assert all(x == 0.0 for x in embedding)