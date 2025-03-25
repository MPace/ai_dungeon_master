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
            yield mock_instance

    @pytest.fixture
    def mock_tokenizer(self):
        """Mock AutoTokenizer from Hugging Face"""
        with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
            mock_instance = MagicMock()
            mock_tokenizer.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def embedding_service(self, mock_model, mock_tokenizer):
        """Create an EmbeddingService with mocked dependencies"""
        with patch('torch.cuda.is_available', return_value=False):
            service = EmbeddingService(model_name="test-model")
            return service

    def test_initialization(self, embedding_service):
        """Test that EmbeddingService initializes correctly"""
        assert embedding_service is not None
        assert embedding_service.model_name == "test-model"
        assert embedding_service.embedding_dim == 384

    def test_generate_embedding(self, embedding_service):
        """Test generating an embedding from text"""
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer output
            mock_tokenize.return_value = {
                'input_ids': torch.ones((1, 10), dtype=torch.long),
                'attention_mask': torch.ones((1, 10), dtype=torch.long)
            }

            # Mock model output
            mock_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((1, 10, 384), dtype=torch.float) * 0.5
            })()
            embedding_service.model.return_value = mock_output

            # Call the function
            embedding = embedding_service.generate_embedding("This is a test text")
            
            # Verify the output
            assert isinstance(embedding, list)
            assert len(embedding) == 384
            assert all(isinstance(x, float) for x in embedding)

    def test_embedding_caching(self, embedding_service):
        """Test that embeddings are cached and reused"""
        test_text = "This is a test for caching"
        
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer output
            mock_tokenize.return_value = {
                'input_ids': torch.ones((1, 10), dtype=torch.long),
                'attention_mask': torch.ones((1, 10), dtype=torch.long)
            }

            # Mock model output
            mock_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((1, 10, 384), dtype=torch.float) * 0.5
            })()
            embedding_service.model.return_value = mock_output

            # First call should compute the embedding
            first_embedding = embedding_service.generate_embedding(test_text)

            # Second call should use the cache
            second_embedding = embedding_service.generate_embedding(test_text)

            # Both should be identical
            assert first_embedding == second_embedding

            # Check cache stats
            cache_stats = embedding_service.get_cache_stats()
            assert cache_stats['cache_hits'] == 1
            assert cache_stats['cache_misses'] == 1  # From the first call

    def test_generate_batch_embeddings(self, embedding_service):
        """Test generating embeddings for a batch of texts"""
        texts = ["First test text", "Second test text", "Third test text"]
        
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer output
            mock_tokenize.return_value = {
                'input_ids': torch.ones((3, 10), dtype=torch.long),
                'attention_mask': torch.ones((3, 10), dtype=torch.long)
            }

            # Mock model output
            mock_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((3, 10, 384), dtype=torch.float) * 0.5
            })()
            embedding_service.model.return_value = mock_output

            # Generate batch embeddings
            embeddings = embedding_service.generate_batch_embeddings(texts)
            
            # Check results
            assert len(embeddings) == 3
            assert all(len(emb) == 384 for emb in embeddings)

    def test_fallback_behavior(self, embedding_service):
        """Test fallback behavior when model fails"""
        with patch.object(embedding_service.model, '__call__', side_effect=Exception("Model error")):
            # It should return a zero vector without failing
            embedding = embedding_service.generate_embedding("This should cause an error")
            
            # Check that we got a zero vector of the correct size
            assert len(embedding) == 384
            assert all(x == 0.0 for x in embedding)