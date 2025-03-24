"""
Tests for the Enhanced Memory Service
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta
from app.services.memory_service_enhanced import EnhancedMemoryService
from app.services.memory_interfaces import ShortTermMemoryInterface, LongTermMemoryInterface, SemanticMemoryInterface

class TestEnhancedMemoryService:
    """Test suite for EnhancedMemoryService"""

    @pytest.fixture
    def mock_db(self):
        """Mock MongoDB connection"""
        with patch('app.extensions.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_db.memory_vectors = mock_collection
            mock_get_db.return_value = mock_db
            yield mock_db

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock EmbeddingService"""
        with patch('app.extensions.get_embedding_service') as mock_get_service:
            mock_service = MagicMock()
            # Configure mock to return predictable embeddings
            mock_service.generate_embedding.return_value = [0.1] * 384
            mock_get_service.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def memory_service(self):
        """Create an EnhancedMemoryService with mocked interfaces"""
        # Mock the memory interfaces
        with patch('app.services.memory_interfaces.ShortTermMemoryInterface') as mock_short_term, \
             patch('app.services.memory_interfaces.LongTermMemoryInterface') as mock_long_term, \
             patch('app.services.memory_interfaces.SemanticMemoryInterface') as mock_semantic:
             
            # Create service with mocked interfaces
            service = EnhancedMemoryService()
            
            # Replace interfaces with mocks
            service.short_term = mock_short_term.return_value
            service.long_term = mock_long_term.return_value
            service.semantic = mock_semantic.return_value
            
            yield service

    def test_initialization(self):
        """Test that EnhancedMemoryService initializes correctly"""
        service = EnhancedMemoryService()
        assert service is not None
        assert isinstance(service.short_term, ShortTermMemoryInterface)
        assert isinstance(service.long_term, LongTermMemoryInterface)
        assert isinstance(service.semantic, SemanticMemoryInterface)

    def test_store_memory_with_text_short_term(self, memory_service, mock_embedding_service):
        """Test storing a short-term memory with text"""
        # Setup
        content = "This is a short-term memory"
        session_id = "test-session"
        metadata = {"test": "value"}
        
        # Configure mock to return success
        memory_service.short_term.store.return_value = {'success': True, 'memory': MagicMock()}
        
        # Call the function
        result = memory_service.store_memory_with_text(
            content=content,
            memory_type='short_term',
            session_id=session_id,
            metadata=metadata
        )
        
        # Verify
        assert result['success'] is True
        assert 'memory' in result
        
        # Verify embedding service was called
        assert mock_embedding_service.generate_embedding.called
        assert mock_embedding_service.generate_embedding.call_args[0][0] == content
        
        # Verify the right interface method was called with correct args
        assert memory_service.short_term.store.called
        call_args = memory_service.short_term.store.call_args[1]
        assert call_args['content'] == content
        assert call_args['session_id'] == session_id
        assert call_args['metadata'] == metadata

    def test_store_memory_with_text_long_term(self, memory_service, mock_embedding_service):
        """Test storing a long-term memory with text"""
        # Setup
        content = "This is a long-term memory"
        session_id = "test-session"
        
        # Configure mock to return success
        memory_service.long_term.store.return_value = {'success': True, 'memory': MagicMock()}
        
        # Call the function
        result = memory_service.store_memory_with_text(
            content=content,
            memory_type='long_term',
            session_id=session_id
        )
        
        # Verify
        assert result['success'] is True
        assert 'memory' in result
        assert memory_service.long_term.store.called

    def test_store_memory_with_text_semantic(self, memory_service, mock_embedding_service):
        """Test storing a semantic memory with text"""
        # Setup
        content = "This is a semantic memory"
        metadata = {
            "concept_type": "npc",
            "relationships": [{"type": "friend", "entity": "Bob"}]
        }
        
        # Configure mock to return success
        memory_service.semantic.store.return_value = {'success': True, 'memory': MagicMock()}
        
        # Call the function
        result = memory_service.store_memory_with_text(
            content=content,
            memory_type='semantic',
            metadata=metadata
        )
        
        # Verify
        assert result['success'] is True
        assert 'memory' in result
        
        # Verify semantic store was called with the right parameters
        assert memory_service.semantic.store.called
        call_args = memory_service.semantic.store.call_args[1]
        assert call_args['content'] == content
        assert call_args['concept_type'] == "npc"
        assert call_args['relationships'] == [{"type": "friend", "entity": "Bob"}]

    def test_retrieve_memories(self, memory_service, mock_embedding_service):
        """Test retrieving memories across different memory types"""
        # Setup
        query = "Find memories related to this"
        session_id = "test-session"
        
        # Setup mock returns for each interface
        short_term_memories = [MagicMock(similarity=0.9), MagicMock(similarity=0.8)]
        long_term_memories = [MagicMock(similarity=0.85)]
        semantic_memories = [MagicMock(similarity=0.95)]
        
        memory_service.short_term.retrieve.return_value = short_term_memories
        memory_service.long_term.retrieve.return_value = long_term_memories
        memory_service.semantic.retrieve.return_value = semantic_memories
        
        # Call the function
        result = memory_service.retrieve_memories(
            query=query,
            session_id=session_id,
            memory_types=['short_term', 'long_term', 'semantic']
        )
        
        # Verify
        assert result['success'] is True
        assert 'results_by_type' in result
        assert 'combined_results' in result
        
        # Check that we got all memory types
        assert 'short_term' in result['results_by_type']
        assert 'long_term' in result['results_by_type']
        assert 'semantic' in result['results_by_type']
        
        # Check that combined results are sorted by similarity
        combined = result['combined_results']
        assert len(combined) > 0
        
        # Verify embedding service was called
        assert mock_embedding_service.generate_embedding.called
        assert mock_embedding_service.generate_embedding.call_args[0][0] == query
        
        # Verify each interface was called with the right parameters
        embedding = mock_embedding_service.generate_embedding.return_value
        memory_service.short_term.retrieve.assert_called_with(
            query_embedding=embedding,
            session_id=session_id,
            limit=3,
            min_similarity=0.7
        )
        memory_service.long_term.retrieve.assert_called_with(
            query_embedding=embedding,
            character_id=None,
            limit=3,
            min_similarity=0.7
        )
        memory_service.semantic.retrieve.assert_called_with(
            query_embedding=embedding,
            character_id=None,
            limit=3,
            min_similarity=0.7
        )

    def test_build_memory_context(self, memory_service, mock_embedding_service):
        """Test building memory context for AI prompts"""
        # Setup
        current_message = "What were we talking about yesterday?"
        session_id = "test-session"
        
        # Mock retrieve_memories to return some test memories
        mock_memories = {
            'success': True,
            'combined_results': [
                {
                    'content': 'We discussed the ancient artifact yesterday.',
                    'memory_type': 'short_term',
                    'similarity': 0.9,
                    'importance': 7,
                    'created_at': datetime.utcnow() - timedelta(days=1)
                },
                {
                    'content': 'The artifact was found in the old temple.',
                    'memory_type': 'long_term',
                    'similarity': 0.85,
                    'importance': 8,
                    'created_at': datetime.utcnow() - timedelta(days=3)
                },
                {
                    'content': 'The Guardian is an ancient spirit protecting the artifact.',
                    'memory_type': 'semantic',
                    'similarity': 0.75,
                    'importance': 9,
                    'created_at': datetime.utcnow() - timedelta(days=2)
                }
            ]
        }
        
        with patch.object(memory_service, 'retrieve_memories') as mock_retrieve:
            mock_retrieve.return_value = mock_memories
            
            # Call the function
            context = memory_service.build_memory_context(
                current_message=current_message,
                session_id=session_id
            )
            
            # Verify
            assert context is not None
            assert isinstance(context, str)
            assert "RELEVANT MEMORIES" in context
            
            # Verify retrieve_memories was called with the right parameters
            mock_retrieve.assert_called_with(
                query=current_message,
                session_id=session_id,
                character_id=None,
                memory_types=['short_term', 'long_term', 'semantic'],
                limit_per_type=5
            )
            
            # Verify that each memory type prefix appears in the context
            assert "Recent memory: " in context
            assert "Important memory: " in context
            assert "Known fact: " in context

    def test_promote_to_long_term(self, memory_service, mock_db):
        """Test promoting a short-term memory to long-term"""
        # Setup
        memory_id = "test-memory-id"
        mock_memory = {
            "memory_id": memory_id,
            "memory_type": "short_term",
            "content": "This memory should be important",
            "embedding": [0.1] * 384,
            "session_id": "test-session",
            "importance": 7,
            "created_at": datetime.utcnow() - timedelta(days=1)
        }
        
        # Configure mock for find_one
        mock_db.memory_vectors.find_one.return_value = mock_memory
        mock_db.memory_vectors.insert_one.return_value.inserted_id = "new-id"
        
        # Call the function
        result = memory_service.promote_to_long_term(memory_id)
        
        # Verify
        assert result is True
        
        # Verify find_one was called with correct parameters
        mock_db.memory_vectors.find_one.assert_called_with({
            'memory_id': memory_id,
            'memory_type': 'short_term'
        })
        
        # Verify insert_one was called with updated memory data
        inserted_memory = mock_db.memory_vectors.insert_one.call_args[0][0]
        assert inserted_memory['memory_id'] == memory_id
        assert inserted_memory['memory_type'] == 'long_term'
        
        # Verify the original memory was deleted
        mock_db.memory_vectors.delete_one.assert_called_with({'_id': mock_memory['_id']})

    def test_check_summarization_triggers_volume_based(self, memory_service, mock_db):
        """Test volume-based summarization triggers"""
        # Setup
        session_id = "test-session"
        
        # Configure mock to return a count above the threshold
        mock_db.memory_vectors.count_documents.return_value = 60  # Above the 50 threshold
        
        # Call the function
        result = memory_service.check_summarization_triggers(session_id)
        
        # Verify
        assert result is True
        
        # Verify count_documents was called with correct parameters
        mock_db.memory_vectors.count_documents.assert_called_with({
            'session_id': session_id,
            'memory_type': 'short_term'
        })

    def test_check_summarization_triggers_time_based(self, memory_service, mock_db):
        """Test time-based summarization triggers"""
        # Setup
        session_id = "test-session"
        
        # Configure mock to return a count below volume threshold
        mock_db.memory_vectors.count_documents.return_value = 15  # Below the 50 threshold
        
        # Configure mock to return an old memory
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        mock_db.memory_vectors.find_one.return_value = {
            "session_id": session_id,
            "memory_type": "short_term",
            "created_at": two_hours_ago
        }
        
        # Call the function
        result = memory_service.check_summarization_triggers(session_id)
        
        # Verify
        assert result is True
        
        # Verify find_one was called with correct parameters and sort
        mock_db.memory_vectors.find_one.assert_called_with(
            {
                'session_id': session_id,
                'memory_type': 'short_term'
            },
            sort=[('created_at', 1)]
        )

    def test_check_summarization_triggers_no_trigger(self, memory_service, mock_db):
        """Test no summarization triggers activated"""
        # Setup
        session_id = "test-session"
        
        # Configure mock to return a count below threshold
        mock_db.memory_vectors.count_documents.return_value = 5  # Below thresholds
        
        # Configure mock to return a recent memory
        thirty_mins_ago = datetime.utcnow() - timedelta(minutes=30)
        mock_db.memory_vectors.find_one.return_value = {
            "session_id": session_id,
            "memory_type": "short_term",
            "created_at": thirty_mins_ago
        }
        
        # Call the function
        result = memory_service.check_summarization_triggers(session_id)
        
        # Verify no trigger activated
        assert result is False