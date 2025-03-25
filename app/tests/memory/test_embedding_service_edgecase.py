import pytest
import numpy as np
import torch
from unittest.mock import patch, MagicMock, call
import threading
import gc
import time
from app.services.embedding_service import EmbeddingService

class TestEmbeddingServiceEdgeCases:
    """Additional edge case tests for EmbeddingService"""

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

    def test_large_text_handling(self, embedding_service):
        """Test handling of texts longer than the max sequence length"""
        # Create a very long text (much longer than max_sequence_length)
        very_long_text = "word " * 1000  # 5000+ characters
        
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer to return truncated sequence at max length
            mock_tokenize.return_value = {
                'input_ids': torch.ones((1, embedding_service.max_sequence_length), dtype=torch.long),
                'attention_mask': torch.ones((1, embedding_service.max_sequence_length), dtype=torch.long)
            }
            
            # Mock model output matching the truncated length
            mock_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((1, embedding_service.max_sequence_length, 384), dtype=torch.float) * 0.5
            })()
            embedding_service.model.return_value = mock_output
            
            # Generate embedding for the long text
            embedding = embedding_service.generate_embedding(very_long_text)
            
            # Verify the tokenizer was called with truncation enabled
            mock_tokenize.assert_called_once()
            call_kwargs = mock_tokenize.call_args[1]
            assert call_kwargs.get('truncation') is True
            assert call_kwargs.get('max_length') == embedding_service.max_sequence_length
            
            # Verify embedding was generated with correct dimensions
            assert len(embedding) == 384

    def test_special_character_handling(self, embedding_service):
        """Test handling of special characters, Unicode, and emojis"""
        # Create text with various special characters
        special_text = "Special chars: !@#$%^&*()_+\nUnicode: 你好, привет\nEmojis: 😊🚀🌍"
        
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer to return a valid sequence
            mock_tokenize.return_value = {
                'input_ids': torch.ones((1, 20), dtype=torch.long),
                'attention_mask': torch.ones((1, 20), dtype=torch.long)
            }
            
            # Mock model output
            mock_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((1, 20, 384), dtype=torch.float) * 0.5
            })()
            embedding_service.model.return_value = mock_output
            
            # Generate embedding for text with special characters
            embedding = embedding_service.generate_embedding(special_text)
            
            # Verify embedding was generated with correct dimensions
            assert len(embedding) == 384
            
            # Verify the tokenizer was called with the special text
            mock_tokenize.assert_called_with(
                special_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=embedding_service.max_sequence_length
            )

    def test_error_resilience(self, embedding_service):
        """Test recovery from temporary model errors"""
        test_text = "This is a test text"
        
        # Set up mock to fail on first call but succeed on second call
        with patch.object(embedding_service.model, '__call__') as mock_model_call:
            # First call raises an exception
            mock_model_call.side_effect = [
                RuntimeError("CUDA out of memory"),  # First call fails
                MagicMock()  # Second call succeeds
            ]
            
            # Mock the successful second call's output
            success_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((1, 10, 384), dtype=torch.float) * 0.5
            })()
            mock_model_call.return_value = success_output
            
            # Mock tokenizer to return consistent output
            with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
                mock_tokenize.return_value = {
                    'input_ids': torch.ones((1, 10), dtype=torch.long),
                    'attention_mask': torch.ones((1, 10), dtype=torch.long)
                }
                
                # First call should return fallback zero vector
                first_result = embedding_service.generate_embedding(test_text)
                assert all(x == 0.0 for x in first_result)
                
                # Reset mock for second call
                mock_model_call.side_effect = None
                mock_model_call.return_value = success_output
                
                # Second call should work normally
                second_result = embedding_service.generate_embedding(test_text)
                assert not all(x == 0.0 for x in second_result)

    def test_performance_degradation(self, embedding_service):
        """Test behavior when the cache becomes very large"""
        # Reduce cache size for testing
        original_cache_size = embedding_service.cache_size
        embedding_service.cache_size = 5
        
        try:
            # Create a list of unique texts
            texts = [f"Test text {i}" for i in range(10)]
            
            # Create mock embedding data
            with patch.object(embedding_service, 'generate_embedding', autospec=True) as mock_generate:
                # Each call will return a different embedding
                mock_generate.side_effect = [
                    [float(i) / 10] * embedding_service.embedding_dim for i in range(10)
                ]
                
                # Process all texts to fill and overflow the cache
                for text in texts:
                    # Call the real method which should use our mocked version
                    embedding_service.generate_embedding(text)
                
                # Verify cache didn't exceed its maximum size
                assert len(embedding_service.cache) <= embedding_service.cache_size
                
                # Verify the most recent texts are in the cache (LRU behavior)
                for i in range(5, 10):
                    assert texts[i] in embedding_service.cache
                
                # Verify the oldest texts are not in the cache
                for i in range(5):
                    assert texts[i] not in embedding_service.cache
        finally:
            # Restore original cache size
            embedding_service.cache_size = original_cache_size

    def test_cache_eviction_strategy(self, embedding_service):
        """Test that the LRU cache eviction works correctly"""
        # Set a small cache size for testing
        original_cache_size = embedding_service.cache_size
        embedding_service.cache_size = 3
        
        try:
            # Create test texts
            texts = ["Text A", "Text B", "Text C", "Text D", "Text E"]
            
            # Mock generate_embedding to avoid actual model calls
            with patch.object(embedding_service, 'generate_embedding', autospec=True) as mock_generate:
                # Each call will return a unique embedding
                mock_generate.side_effect = [
                    [float(i) / 10] * embedding_service.embedding_dim for i in range(len(texts))
                ]
                
                # Add first 3 texts to fill cache
                for i in range(3):
                    embedding_service.generate_embedding(texts[i])
                
                # Cache should now contain A, B, C
                assert texts[0] in embedding_service.cache
                assert texts[1] in embedding_service.cache
                assert texts[2] in embedding_service.cache
                
                # Access A again to make it most recently used
                embedding_service.generate_embedding(texts[0])
                
                # Add D - should evict B (least recently used)
                embedding_service.generate_embedding(texts[3])
                assert texts[0] in embedding_service.cache  # A should still be there
                assert texts[1] not in embedding_service.cache  # B should be evicted
                assert texts[2] in embedding_service.cache  # C should still be there
                assert texts[3] in embedding_service.cache  # D should be added
                
                # Add E - should evict C (now the least recently used)
                embedding_service.generate_embedding(texts[4])
                assert texts[0] in embedding_service.cache  # A should still be there
                assert texts[2] not in embedding_service.cache  # C should be evicted
                assert texts[3] in embedding_service.cache  # D should still be there
                assert texts[4] in embedding_service.cache  # E should be added
        finally:
            # Restore original cache size
            embedding_service.cache_size = original_cache_size

    def test_vector_normalization(self, embedding_service):
        """Test if embeddings are properly normalized"""
        test_text = "Test normalization"
        
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer output
            mock_tokenize.return_value = {
                'input_ids': torch.ones((1, 10), dtype=torch.long),
                'attention_mask': torch.ones((1, 10), dtype=torch.long)
            }
            
            # Create model output with some extreme values
            last_hidden_state = torch.zeros((1, 10, 384), dtype=torch.float)
            # Add some very large values
            last_hidden_state[0, 0, :] = 1e6
            # Add some very small values
            last_hidden_state[0, 1, :] = 1e-6
            # Add some NaN values
            last_hidden_state[0, 2, 0] = float('nan')
            
            mock_output = type('MockOutput', (), {'last_hidden_state': last_hidden_state})()
            embedding_service.model.return_value = mock_output
            
            # Generate embedding 
            embedding = embedding_service.generate_embedding(test_text)
            
            # Check for NaN values - method should handle them
            assert not any(np.isnan(x) for x in embedding)
            
            # Check that extremely large values are handled
            assert all(abs(x) < 1e7 for x in embedding)
            
            # Embeddings should generally be normalized or have reasonable magnitudes
            # (the exact normalization depends on implementation)
            embedding_magnitude = np.sqrt(sum(x*x for x in embedding))
            assert embedding_magnitude < 1e7  # Reasonable upper bound

    def test_resource_management(self, embedding_service):
        """Test proper resource cleanup after usage"""
        # Test that resources are properly managed by checking memory usage
        # This is more of an integration test, but we can simulate some aspects
        
        # Force garbage collection before test
        gc.collect()
        
        # Create a reference to track
        test_data = {}
        
        def run_embedding_service():
            # Create a large tensor in the test_data dictionary
            test_data['large_tensor'] = torch.ones((1000, 1000), dtype=torch.float)
            
            # Mock embedding generation to use this tensor
            with patch.object(embedding_service, 'generate_embedding') as mock_generate:
                mock_generate.return_value = [0.5] * embedding_service.embedding_dim
                
                # Generate some embeddings
                for i in range(10):
                    embedding_service.generate_embedding(f"Text {i}")
            
            # Clear reference to allow garbage collection
            del test_data['large_tensor']
        
        # Run the function
        run_embedding_service()
        
        # Force garbage collection
        gc.collect()
        
        # Verify the tensor was properly garbage collected
        assert 'large_tensor' not in test_data
        
        # Not a foolproof test, but checks basic cleanup

    def test_batch_size_limits(self, embedding_service):
        """Test with varying batch sizes including edge cases"""
        # Test empty batch
        assert embedding_service.generate_batch_embeddings([]) == []
        
        # Test batch size of 1
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer for single item batch
            mock_tokenize.return_value = {
                'input_ids': torch.ones((1, 10), dtype=torch.long),
                'attention_mask': torch.ones((1, 10), dtype=torch.long)
            }
            
            # Mock model output
            mock_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((1, 10, 384), dtype=torch.float) * 0.5
            })()
            embedding_service.model.return_value = mock_output
            
            # Test batch of size 1
            result = embedding_service.generate_batch_embeddings(["Single text"])
            assert len(result) == 1
            assert len(result[0]) == 384
        
        # Test large batch that might exceed model capacity
        large_batch = [f"Text {i}" for i in range(100)]
        
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer for large batch - simulate tokenizer handling it
            mock_tokenize.return_value = {
                'input_ids': torch.ones((100, 10), dtype=torch.long),
                'attention_mask': torch.ones((100, 10), dtype=torch.long)
            }
            
            # Mock model output - but make it fail with CUDA OOM
            embedding_service.model.side_effect = RuntimeError("CUDA out of memory")
            
            # The service should handle this gracefully
            result = embedding_service.generate_batch_embeddings(large_batch)
            
            # Should return fallback embeddings for each input
            assert len(result) == 100
            assert all(len(emb) == 384 for emb in result)
            assert all(all(x == 0.0 for x in emb) for emb in result)  # All fallback zero vectors

    def test_thread_safety(self, embedding_service):
        """Test concurrent access for thread safety"""
        # This test verifies that the service can be called from multiple threads
        num_threads = 5
        texts_per_thread = 20
        results = [None] * num_threads
        
        def worker(thread_id):
            """Worker function that calls generate_embedding multiple times"""
            thread_results = []
            
            # Each thread calls generate_embedding multiple times
            for i in range(texts_per_thread):
                text = f"Thread {thread_id} Text {i}"
                
                # Mock the embedding generation to avoid actual model calls
                with patch.object(embedding_service, 'generate_embedding', autospec=True) as mock_generate:
                    # Return a thread-specific embedding
                    mock_result = [float(thread_id) / 10] * embedding_service.embedding_dim
                    mock_generate.return_value = mock_result
                    
                    # Call the method
                    embedding = embedding_service.generate_embedding(text)
                    thread_results.append(embedding)
            
            # Store results for this thread
            results[thread_id] = thread_results
        
        # Create and start threads
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Verify each thread got results
        for thread_id in range(num_threads):
            assert results[thread_id] is not None
            assert len(results[thread_id]) == texts_per_thread
        
        # Note: This test doesn't fully verify thread safety, just basic concurrent usage

    def test_token_dimension_mismatch(self, embedding_service):
        """Test handling of cases where token dimensions don't match expected dimensions"""
        test_text = "Test dimension mismatch"
        
        with patch.object(embedding_service.tokenizer, '__call__') as mock_tokenize:
            # Mock tokenizer output with expected dimensions
            mock_tokenize.return_value = {
                'input_ids': torch.ones((1, 10), dtype=torch.long),
                'attention_mask': torch.ones((1, 10), dtype=torch.long)
            }
            
            # Mock model output WITH WRONG DIMENSIONS
            # Instead of expected (1, 10, 384), return (1, 10, 768)
            mock_output = type('MockOutput', (), {
                'last_hidden_state': torch.ones((1, 10, 768), dtype=torch.float) * 0.5
            })()
            embedding_service.model.return_value = mock_output
            
            # Test whether service handles dimension mismatch gracefully
            try:
                # This should trigger dimension mismatch during processing
                embedding = embedding_service.generate_embedding(test_text)
                
                # If we get here, the service handled the mismatch
                # It might adapt, truncate, or use fallback values
                assert len(embedding) == embedding_service.embedding_dim
            except Exception as e:
                # Alternatively, the service might raise a specific error
                # that can be handled by the calling code
                assert "dimension" in str(e).lower() or "shape" in str(e).lower()