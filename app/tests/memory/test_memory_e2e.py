"""
End-to-End Tests for Memory System
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import uuid
from app.services.embedding_service import EmbeddingService
from app.services.memory_service_enhanced import EnhancedMemoryService
from app.services.summarization_service import SummarizationService
from app.services.langchain_service import LangchainService
from app.services.ai_service import AIService
from app.models.memory_vector import MemoryVector
from app.models.ai_response import AIResponse

class TestMemoryE2E:
    """End-to-End tests for the memory system"""

    @pytest.fixture
    def mock_db(self):
        """Mock MongoDB connection"""
        with patch('app.extensions.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_memory_collection = MagicMock()
            mock_db.memory_vectors = mock_memory_collection
            mock_get_db.return_value = mock_db
            yield mock_db

    @pytest.fixture
    def session_data(self):
        """Create test session data"""
        return {
            'session_id': str(uuid.uuid4()),
            'character_id': str(uuid.uuid4()),
            'user_id': str(uuid.uuid4())
        }

    @pytest.fixture
    def memory_setup(self, mock_db, session_data):
        """Set up test memory data in the mock database"""
        # Memories for the session
        memories = [
            {
                'memory_id': f"memory-{i}",
                'session_id': session_data['session_id'],
                'character_id': session_data['character_id'],
                'user_id': session_data['user_id'],
                'content': f"Test memory {i} about the quest",
                'memory_type': 'short_term' if i < 8 else 'long_term',
                'embedding': [0.1] * 384,
                'importance': min(10, 5 + i % 6),
                'created_at': datetime.utcnow() - timedelta(hours=i),
                'metadata': {'sender': 'player' if i % 2 == 0 else 'dm'}
            }
            for i in range(10)
        ]
        
        # Configure find to return specific slices of memories based on query
        def mock_find_impl(query=None, **kwargs):
            if query is None:
                query = {}
            
            # Filter by session_id
            if 'session_id' in query:
                results = [m for m in memories if m['session_id'] == query['session_id']]
            else:
                results = memories.copy()
            
            # Filter by memory_type
            if 'memory_type' in query:
                if isinstance(query['memory_type'], str):
                    results = [m for m in results if m['memory_type'] == query['memory_type']]
                elif '$in' in query['memory_type']:
                    results = [m for m in results if m['memory_type'] in query['memory_type']['$in']]
            
            # Create a custom list with sort and limit methods
            class MockCursor(list):
                def sort(self, sort_params, **kwargs):
                    # Simple sorting by created_at
                    if sort_params[0][0] == 'created_at':
                        reverse = sort_params[0][1] == -1
                        sorted_results = sorted(self, key=lambda x: x['created_at'], reverse=reverse)
                        return MockCursor(sorted_results)
                    return self
                
                def limit(self, limit_val):
                    return MockCursor(self[:limit_val])
            
            return MockCursor(results)
        
        mock_db.memory_vectors.find = mock_find_impl
        
        # Configure count_documents to return predictable counts
        mock_db.memory_vectors.count_documents.return_value = len([m for m in memories 
                                                              if m['memory_type'] == 'short_term' and 
                                                              m['session_id'] == session_data['session_id']])
        
        # Configure find_one to return the first matching memory
        def mock_find_one_impl(query=None, **kwargs):
            if query is None:
                query = {}
                
            for memory in memories:
                match = True
                for key, value in query.items():
                    if key not in memory or memory[key] != value:
                        match = False
                        break
                
                if match:
                    return memory
            
            return None
        
        mock_db.memory_vectors.find_one = mock_find_one_impl
        
        # Return session data
        return session_data

    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock EmbeddingService that returns predictable embeddings"""
        with patch('app.extensions.get_embedding_service') as mock_get_service:
            mock_service = MagicMock(spec=EmbeddingService)
            
            # Make generate_embedding return different embeddings for different texts
            # using a simple hash function to get consistent but different values
            def mock_generate_embedding(text):
                import hashlib
                # Create a hash of the text
                hash_obj = hashlib.md5(text.encode())
                hash_bytes = hash_obj.digest()
                
                # Turn the hash into an embedding vector
                embedding = []
                for i in range(384):  # Create a 384-dim vector
                    # Get a value from the hash or cycle through it
                    hash_index = i % len(hash_bytes)
                    # Normalize to range [-1, 1]
                    value = (hash_bytes[hash_index] - 128) / 128
                    embedding.append(value)
                
                return embedding
            
            mock_service.generate_embedding.side_effect = mock_generate_embedding
            mock_get_service.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def mock_summarization_service(self):
        """Create a mock SummarizationService"""
        with patch('app.services.summarization_service.SummarizationService', autospec=True) as MockSummarizationService:
            mock_service = MockSummarizationService.return_value
            mock_service.summarize_text.return_value = "This is a summarized version of all the memories."
            yield mock_service

    @pytest.fixture
    def memory_service(self, mock_embedding_service):
        """Create an EnhancedMemoryService with real components but mocked DB"""
        service = EnhancedMemoryService()
        return service

    def test_e2e_memory_storage_and_retrieval(self, memory_service, memory_setup, mock_db):
        """Test end-to-end memory storage and retrieval flow"""
        # Get test session data
        session = memory_setup
        
        # 1. Store a player message
        player_message = "I want to investigate the ancient temple we found yesterday."
        
        # Store the memory
        player_result = memory_service.store_memory_with_text(
            content=player_message,
            memory_type='short_term',
            session_id=session['session_id'],
            character_id=session['character_id'],
            user_id=session['user_id'],
            metadata={'sender': 'player'}
        )
        
        # Verify
        assert player_result['success'] is True
        assert isinstance(player_result['memory'], MemoryVector)
        assert player_result['memory'].content == player_message
        
        # 2. Store a DM response
        dm_message = "As you approach the temple, you notice ancient symbols carved into the stone archway."
        
        # Store the memory
        dm_result = memory_service.store_memory_with_text(
            content=dm_message,
            memory_type='short_term',
            session_id=session['session_id'],
            character_id=session['character_id'],
            user_id=session['user_id'],
            metadata={'sender': 'dm'}
        )
        
        # Verify
        assert dm_result['success'] is True
        
        # 3. Now retrieve memories for a related query
        query = "What did we find in the temple?"
        
        # Build memory context
        context = memory_service.build_memory_context(
            current_message=query,
            session_id=session['session_id'],
            character_id=session['character_id']
        )
        
        # Verify
        assert context is not None
        assert "RELEVANT MEMORIES" in context
        assert "temple" in context.lower()
        
        # Now check if the memories we just added are included
        assert player_message in context or "investigate the ancient temple" in context
        assert dm_message in context or "ancient symbols carved" in context

    def test_e2e_conversation_with_memory(self, memory_setup, mock_db, mock_embedding_service):
        """Test a full conversation flow with memory integration via Langchain"""
        # Get test session data
        session = memory_setup
        
        # Mock OpenAI for Langchain
        with patch('langchain.chat_models.ChatOpenAI') as MockChatOpenAI:
            mock_llm = MockChatOpenAI.return_value
            mock_llm.predict.return_value = "I remember the temple has ancient symbols on the archway. Let me tell you more about what you see inside..."
            
            # Create Langchain service
            langchain_service = LangchainService(api_key="fake-key")
            
            # Create AI service that uses Langchain
            ai_service = AIService(use_langchain=True)
            ai_service.langchain_service = langchain_service
            
            # Create a conversation with memory
            character_data = {
                'name': 'Tordek',
                'race': 'Dwarf',
                'class': 'Fighter',
                'character_id': session['character_id'],
                'user_id': session['user_id']
            }
            
            conversation_history = [
                {'sender': 'player', 'message': "I want to explore the temple."},
                {'sender': 'dm', 'message': "You approach the ancient temple with caution."}
            ]
            
            # Player sends a new message
            player_message = "What do I remember about this temple?"
            
            # Generate response using AI service
            response = ai_service.generate_response(
                player_message=player_message,
                conversation_history=conversation_history,
                character_data=character_data,
                game_state="exploration"
            )
            
            # Verify
            assert isinstance(response, AIResponse)
            assert "temple" in response.response_text.lower()
            assert "ancient symbols" in response.response_text.lower()

    def test_e2e_memory_summarization(self, memory_setup, mock_db, mock_embedding_service, mock_summarization_service):
        """Test end-to-end memory summarization process"""
        # Get test session data
        session = memory_setup
        
        # Create summarization service with the mock
        summarization_service = SummarizationService()
        summarization_service.summarizer = mock_summarization_service.summarizer
        
        # Increase memory count to trigger volume-based summarization
        mock_db.memory_vectors.count_documents.return_value = 60  # Above threshold
        
        # Patch Memory Service to use our mocks
        with patch('app.services.memory_service.MemoryService.create_memory_summary') as mock_create_summary:
            # Mock summarization result
            mock_memory = MagicMock()
            mock_memory.memory_id = 'summary1'
            mock_create_summary.return_value = {'success': True, 'memory': mock_memory}
            
            # Check if summarization should be triggered
            memory_service = EnhancedMemoryService()
            should_summarize = memory_service.check_summarization_triggers(session['session_id'])
            
            # Verify
            assert should_summarize is True
            
            # Trigger summarization
            result = summarization_service.trigger_summarization_if_needed(session['session_id'])
            
            # Verify
            assert result['success'] is True
            
            # Mock back to lower count
            mock_db.memory_vectors.count_documents.return_value = 5
            
            # Check again - should not trigger
            should_summarize = memory_service.check_summarization_triggers(session['session_id'])
            assert should_summarize is False