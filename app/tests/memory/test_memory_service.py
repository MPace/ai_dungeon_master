"""
Tests for the Memory Service
"""
import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from datetime import datetime
from app.services.memory_service import MemoryService
from app.models.memory_vector import MemoryVector

class TestMemoryService:
    """Test suite for MemoryService"""

    @pytest.fixture
    def mock_db(self):
        """Mock MongoDB connection"""
        with patch('app.services.memory_service.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_db.memory_vectors = mock_collection
            mock_get_db.return_value = mock_db
            yield mock_db

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock EmbeddingService"""
        with patch('app.services.memory_service.get_embedding_service') as mock_get_service:
            mock_service = MagicMock()
            # Configure the mock to return predictable embeddings
            mock_service.generate_embedding.return_value = [0.1] * 384
            mock_get_service.return_value = mock_service
            yield mock_service

    def test_store_memory(self, mock_db):
        """Test storing a memory"""
        # Setup
        session_id = "test-session"
        content = "This is a test memory"
        embedding = [0.1] * 384
        
        # Configure mock to return success
        mock_db.memory_vectors.insert_one.return_value.inserted_id = "mock-id"
        
        # Call the function
        result = MemoryService.store_memory(
            session_id=session_id,
            content=content,
            embedding=embedding,
            memory_type='short_term'
        )
        
        # Verify
        assert result['success'] is True
        assert isinstance(result['memory'], MemoryVector)
        assert result['memory'].content == content
        assert result['memory'].session_id == session_id
        assert mock_db.memory_vectors.insert_one.called
        
        # Verify the inserted document
        inserted_doc = mock_db.memory_vectors.insert_one.call_args[0][0]
        assert inserted_doc['content'] == content
        assert inserted_doc['embedding'] == embedding
        assert inserted_doc['session_id'] == session_id
        assert inserted_doc['memory_type'] == 'short_term'

    def test_store_memory_db_failure(self, mock_db):
        """Test handling of database failure when storing"""
        # Setup
        mock_db.memory_vectors.insert_one.side_effect = Exception("DB error")
        
        # Call the function
        result = MemoryService.store_memory(
            session_id="test-session",
            content="Test content",
            embedding=[0.1] * 384
        )
        
        # Verify
        assert result['success'] is False
        assert 'error' in result

    def test_find_similar_memories_with_vector_search(self, mock_db):
        """Test finding similar memories using vector search"""
        # Setup for vector search
        session_id = "test-session"
        embedding = [0.1] * 384
        
        # Mock the aggregate pipeline result
        mock_memory_data = [
            {
                'content': 'Similar memory 1',
                'session_id': session_id,
                'embedding': [0.1] * 384,
                'memory_id': 'memory1',
                'similarity': 0.95,
                'created_at': datetime.utcnow(),
                '_id': 'ObjectId1'
            },
            {
                'content': 'Similar memory 2',
                'session_id': session_id,
                'embedding': [0.2] * 384,
                'memory_id': 'memory2',
                'similarity': 0.85,
                'created_at': datetime.utcnow(),
                '_id': 'ObjectId2'
            }
        ]
        
        # Configure mock to return our test data
        mock_db.memory_vectors.aggregate.return_value = mock_memory_data
        
        # Call the function
        result = MemoryService.find_similar_memories(
            embedding=embedding,
            session_id=session_id,
            limit=5,
            min_similarity=0.7
        )
        
        # Verify
        assert result['success'] is True
        assert len(result['memories']) == 2
        assert isinstance(result['memories'][0], MemoryVector)
        assert result['memories'][0].content == 'Similar memory 1'
        assert result['memories'][1].content == 'Similar memory 2'
        
        # Check that aggregate was called (no need to verify exact pipeline)
        assert mock_db.memory_vectors.aggregate.called

    def test_find_similar_memories_fallback(self, mock_db):
        """Test fallback similarity search when vector search fails"""
        # Setup
        session_id = "test-session"
        embedding = [0.1] * 384
        
        # Make the aggregate method raise an exception to trigger fallback
        mock_db.memory_vectors.aggregate.side_effect = Exception("Vector search not available")
        
        # Mock the find method for fallback
        mock_memory_data = [
            {
                'content': 'Similar memory 1',
                'session_id': session_id,
                'embedding': [0.1] * 384,
                'memory_id': 'memory1',
                'created_at': datetime.utcnow()
            },
            {
                'content': 'Similar memory 2',
                'session_id': session_id,
                'embedding': [0.2] * 384,
                'memory_id': 'memory2',
                'created_at': datetime.utcnow()
            }
        ]
        mock_db.memory_vectors.find.return_value = mock_memory_data
        
        # Patch the cosine similarity calculation to return predictable values
        with patch.object(MemoryService, '_cosine_similarity') as mock_cosine:
            mock_cosine.side_effect = lambda a, b: 0.95 if a == [0.1] * 384 else 0.85
            
            # Also patch the _fallback_similarity_search method
            with patch.object(MemoryService, '_fallback_similarity_search') as mock_fallback:
                # Set up mock_fallback to return our mock memory data
                for memory in mock_memory_data:
                    memory['similarity'] = 0.95 if memory['memory_id'] == 'memory1' else 0.85
                mock_fallback.return_value = mock_memory_data
                
                # Call the function
                result = MemoryService.find_similar_memories(
                    embedding=embedding,
                    session_id=session_id,
                    limit=5,
                    min_similarity=0.7
                )
                
                # Verify
                assert result['success'] is True
                assert len(result['memories']) == 2
                assert isinstance(result['memories'][0], MemoryVector)
                
                # Verify fallback method was called
                assert mock_fallback.called

    def test_cosine_similarity(self):
        """Test the cosine similarity calculation"""
        # Create test vectors
        vec_a = [1.0, 0.0, 0.0]  # Unit vector along x-axis
        vec_b = [0.0, 1.0, 0.0]  # Unit vector along y-axis
        vec_c = [1.0, 1.0, 0.0]  # Vector in xy-plane
        
        # Calculate similarities
        sim_a_b = MemoryService._cosine_similarity(vec_a, vec_b)
        sim_a_c = MemoryService._cosine_similarity(vec_a, vec_c)
        sim_b_c = MemoryService._cosine_similarity(vec_b, vec_c)
        sim_a_a = MemoryService._cosine_similarity(vec_a, vec_a)
        
        # Verify results
        assert sim_a_b == 0.0  # Orthogonal vectors have 0 similarity
        assert round(sim_a_c, 4) == round(1/np.sqrt(2), 4)  # 45 degree angle
        assert round(sim_b_c, 4) == round(1/np.sqrt(2), 4)  # 45 degree angle
        assert sim_a_a == 1.0  # Same vector has similarity 1

    def test_store_memory_with_text(self, mock_db, mock_embedding_service):
        """Test storing a memory with automatic embedding generation"""
        # Setup
        session_id = "test-session"
        content = "This is a test memory"
        
        # Configure mocks for success
        mock_db.memory_vectors.insert_one.return_value.inserted_id = "mock-id"
        
        # Patch the store_memory method to return success
        with patch.object(MemoryService, 'store_memory') as mock_store_memory:
            mock_memory = MagicMock(spec=MemoryVector)
            mock_store_memory.return_value = {'success': True, 'memory': mock_memory}
            
            # Call the function
            result = MemoryService.store_memory_with_text(
                session_id=session_id,
                content=content,
                memory_type='short_term'
            )
            
            # Verify
            assert result['success'] is True
            assert result['memory'] == mock_memory
            
            # Verify embedding service was called
            assert mock_embedding_service.generate_embedding.called
            assert mock_embedding_service.generate_embedding.call_args[0][0] == content
            
            # Verify store_memory was called
            assert mock_store_memory.called
            embedding = mock_embedding_service.generate_embedding.return_value
            mock_store_memory.assert_called_with(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type='short_term',
                character_id=None,
                user_id=None,
                importance=5,
                metadata=None
            )

    def test_find_similar_memories_by_text(self, mock_db, mock_embedding_service):
        """Test finding similar memories by text"""
        # Setup
        session_id = "test-session"
        query_text = "Find memories similar to this"
        
        # Mock memories to be returned
        mock_memories = [MagicMock(), MagicMock()]
        
        # Patch find_similar_memories to return our mock memories
        with patch.object(MemoryService, 'find_similar_memories') as mock_find:
            mock_find.return_value = {'success': True, 'memories': mock_memories}
            
            # Call the function
            result = MemoryService.find_similar_memories_by_text(
                text=query_text,
                session_id=session_id
            )
            
            # Verify
            assert result['success'] is True
            assert result['memories'] == mock_memories
            
            # Verify embedding service was called correctly
            assert mock_embedding_service.generate_embedding.called
            assert mock_embedding_service.generate_embedding.call_args[0][0] == query_text
            
            # Verify find_similar_memories was called with the right parameters
            embedding = mock_embedding_service.generate_embedding.return_value
            mock_find.assert_called_with(
                embedding=embedding,
                session_id=session_id,
                limit=5,
                min_similarity=0.7
            )

    def test_create_memory_summary(self, mock_db):
        """Test creating a summary memory"""
        # Setup
        session_id = "test-session"
        memory_ids = ["memory1", "memory2", "memory3"]
        summary_content = "This is a summary of multiple memories"
        summary_embedding = [0.1] * 384
        
        # Patch store_memory to return success
        with patch.object(MemoryService, 'store_memory') as mock_store:
            mock_memory = MagicMock()
            mock_store.return_value = {'success': True, 'memory': mock_memory}
            
            # Call the function
            result = MemoryService.create_memory_summary(
                memory_ids=memory_ids,
                summary_content=summary_content,
                summary_embedding=summary_embedding,
                session_id=session_id
            )
            
            # Verify store_memory was called with the right parameters
            mock_store.assert_called_with(
                session_id=session_id,
                content=summary_content,
                embedding=summary_embedding,
                memory_type='summary',
                character_id=None,
                user_id=None,
                importance=8,
                metadata={'summarized_count': len(memory_ids)},
                summary_of=memory_ids
            )
            
            # Result should match what store_memory returned
            assert result == {'success': True, 'memory': mock_memory}