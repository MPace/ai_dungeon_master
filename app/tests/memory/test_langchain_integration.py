"""
Tests for Langchain Integration with Memory System
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.langchain_service import LangchainService
from app.services.memory_service_enhanced import EnhancedMemoryService

class TestLangchainIntegration:
    """Test suite for Langchain integration with memory system"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM model"""
        with patch('langchain.chat_models.ChatOpenAI') as mock_chat_openai:
            mock_instance = MagicMock()
            mock_chat_openai.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_memory_service(self):
        """Mock EnhancedMemoryService"""
        with patch.object(EnhancedMemoryService, '__init__', return_value=None):
            memory_service = EnhancedMemoryService()
            memory_service.build_memory_context = MagicMock()
            memory_service.build_memory_context.return_value = "## RELEVANT MEMORIES:\nRecent memory: The player found a map to the hidden temple.\nImportant memory: The temple contains a powerful artifact."
            memory_service.store_memory_with_text = MagicMock()
            memory_service.store_memory_with_text.return_value = {'success': True}
            yield memory_service

    @pytest.fixture
    def langchain_service(self, mock_llm, mock_memory_service):
        """Create a LangchainService with mocked components"""
        with patch.object(LangchainService, '_create_llm', return_value=mock_llm):
            service = LangchainService(api_key="fake-key", model_name="gpt-3.5-turbo")
            service.memory_service = mock_memory_service
            yield service

    def test_initialization(self, mock_llm):
        """Test LangchainService initialization"""
        with patch.object(LangchainService, '_create_llm', return_value=mock_llm):
            service = LangchainService(api_key="fake-key", model_name="gpt-3.5-turbo")
            assert service is not None
            assert service.api_key == "fake-key"
            assert service.model_name == "gpt-3.5-turbo"
            assert service.llm is mock_llm
            assert service.memory_service is not None

    def test_create_dm_chain(self, langchain_service, mock_llm):
        """Test creating a simple DM chain without memory"""
        # Setup
        system_prompt = "You are a dungeon master."
        character_data = {"name": "Tordek", "race": "Dwarf", "class": "Fighter"}
        
        # Mock LLMChain
        with patch('langchain.chains.LLMChain') as mock_chain_class:
            mock_chain = MagicMock()
            mock_chain_class.return_value = mock_chain
            
            # Call the function
            chain = langchain_service.create_dm_chain(system_prompt, character_data)
            
            # Verify
            assert chain is mock_chain
            assert mock_chain_class.called
            
            # Check that chain was created with the right components
            call_kwargs = mock_chain_class.call_args[1]
            assert call_kwargs['llm'] is mock_llm
            
            # Check that the prompt was created correctly
            prompt = call_kwargs['prompt']
            assert "You are a dungeon master" in prompt.template

    def test_create_memory_enhanced_chain(self, langchain_service, mock_llm, mock_memory_service):
        """Test creating a chain with memory enhancement"""
        # Setup
        system_prompt = "You are a dungeon master."
        character_data = {"name": "Tordek", "race": "Dwarf", "class": "Fighter", "character_id": "char123"}
        session_id = "session456"
        
        # Mock LLMChain
        with patch('langchain.chains.LLMChain') as mock_chain_class:
            mock_chain = MagicMock()
            mock_chain_class.return_value = mock_chain
            
            # Call the function
            chain = langchain_service.create_memory_enhanced_chain(system_prompt, character_data, session_id)
            
            # Verify
            assert chain is mock_chain
            assert mock_chain_class.called
            
            # Check that chain was created with the right components
            call_kwargs = mock_chain_class.call_args[1]
            assert call_kwargs['llm'] is mock_llm
            
            # Check that the prompt includes memory_context placeholder
            prompt = call_kwargs['prompt']
            assert "{memory_context}" in prompt.template
            
            # Check that the memory is the enhanced type
            memory = call_kwargs['memory']
            assert hasattr(memory, 'memory_service')
            assert memory.session_id == session_id
            assert memory.character_id == "char123"

    def test_enhanced_memory_load_variables(self, langchain_service, mock_memory_service):
        """Test loading memory variables with enhanced memory"""
        # Setup
        system_prompt = "You are a dungeon master."
        character_data = {"name": "Tordek", "race": "Dwarf", "class": "Fighter", "character_id": "char123"}
        session_id = "session456"
        
        # Create a chain with enhanced memory
        with patch('langchain.chains.LLMChain'):
            chain = langchain_service.create_memory_enhanced_chain(system_prompt, character_data, session_id)
            
            # Get the memory instance from the chain
            memory = chain.memory
            
            # Prepare inputs
            inputs = {"input": "What do I remember about the temple?"}
            
            # Mock the parent class's load_memory_variables
            with patch.object(memory, 'chat_memory'):
                # Call load_memory_variables
                variables = memory.load_memory_variables(inputs)
                
                # Verify
                assert "memory_context" in variables
                assert variables["memory_context"] == mock_memory_service.build_memory_context.return_value
                
                # Verify build_memory_context was called with correct args
                mock_memory_service.build_memory_context.assert_called_with(
                    current_message="What do I remember about the temple?",
                    session_id=session_id,
                    character_id="char123"
                )

    def test_enhanced_memory_save_context(self, langchain_service, mock_memory_service):
        """Test saving context with enhanced memory"""
        # Setup
        system_prompt = "You are a dungeon master."
        character_data = {"name": "Tordek", "race": "Dwarf", "class": "Fighter", "character_id": "char123"}
        session_id = "session456"
        
        # Create a chain with enhanced memory
        with patch('langchain.chains.LLMChain'):
            chain = langchain_service.create_memory_enhanced_chain(system_prompt, character_data, session_id)
            
            # Get the memory instance from the chain
            memory = chain.memory
            
            # Prepare input and output
            inputs = {"input": "Tell me more about the temple."}
            outputs = {"text": "The temple is an ancient structure dedicated to a forgotten god."}
            
            # Mock the parent class's save_context
            with patch.object(memory, 'chat_memory'):
                # Call save_context
                memory.save_context(inputs, outputs)
                
                # Verify both player message and DM response were stored
                assert mock_memory_service.store_memory_with_text.call_count == 2
                
                # Verify player message was stored correctly
                mock_memory_service.store_memory_with_text.assert_any_call(
                    content="Tell me more about the temple.",
                    session_id=session_id,
                    character_id="char123",
                    memory_type="short_term",
                    metadata={"sender": "player"}
                )
                
                # Verify DM response was stored correctly
                mock_memory_service.store_memory_with_text.assert_any_call(
                    content="The temple is an ancient structure dedicated to a forgotten god.",
                    session_id=session_id,
                    character_id="char123",
                    memory_type="short_term",
                    metadata={"sender": "dm"}
                )

    def test_run_chain(self, langchain_service):
        """Test running a chain with memory"""
        # Setup
        mock_chain = MagicMock()
        mock_chain.run.return_value = "The DM's response."
        session_id = "session456"
        message = "What do I see in the temple?"
        
        # Call the function
        result = langchain_service.run_chain(mock_chain, message, session_id)
        
        # Verify
        assert result["response"] == "The DM's response."
        assert result["session_id"] == session_id
        assert mock_chain.run.called
        assert mock_chain.run.call_args[1]["input"] == message

    def test_run_chain_error_handling(self, langchain_service):
        """Test error handling when running a chain"""
        # Setup - make chain raise an exception
        mock_chain = MagicMock()
        mock_chain.run.side_effect = Exception("Chain error")
        
        # Call the function
        result = langchain_service.run_chain(mock_chain, "Test message")
        
        # Verify
        assert "response" in result
        assert "An error occurred" in result["response"]
        assert "Chain error" in result["response"]