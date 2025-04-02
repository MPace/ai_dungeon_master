# app/services/langchain_memory.py
"""
Custom Langchain Memory Classes
"""
import logging
from typing import Dict, Any, List, Optional
from langchain.memory import BaseChatMemory
from app.services.memory_service_enhanced import EnhancedMemoryService

logger = logging.getLogger(__name__)

class VectorDBMemory(BaseChatMemory):
    """Memory class that uses Vector DB for memory storage and retrieval"""
    
    def __init__(self, memory_service=None, session_id=None, character_id=None, 
                 user_id=None, memory_key="history", input_key="input", context_key="memory_context"):
        """Initialize memory with vector DB integration"""
        super().__init__(memory_key=memory_key, input_key=input_key)
        self.memory_service = memory_service or EnhancedMemoryService()
        self.session_id = session_id
        self.character_id = character_id
        self.user_id = user_id
        self.context_key = context_key  # Add new parameter for memory context
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables including relevant memories"""
        # Get standard variables from parent (chat history)
        variables = super().load_memory_variables(inputs)
        
        # Retrieve relevant memories based on input
        query = inputs.get(self.input_key, "")
        
        if query and self.session_id:
            memory_context = self.memory_service.build_memory_context(
                current_message=query,
                session_id=self.session_id,
                character_id=self.character_id
            )
            
            # Add memory_context as a separate variable
            variables[self.context_key] = memory_context or ""
            logger.info(f"Added memory context ({len(memory_context)} chars)")
        else:
            variables[self.context_key] = ""
        
        return variables
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context to memory"""
        # Save to parent's buffer
        super().save_context(inputs, outputs)
        
        # Save to our vector memory
        if self.session_id:
            # Store player message
            player_message = inputs.get(self.input_key, "")
            if player_message:
                self.memory_service.store_memory_with_text(
                    content=player_message,
                    memory_type="short_term",
                    session_id=self.session_id,
                    character_id=self.character_id, 
                    user_id=self.user_id,
                    metadata={"sender": "player"}
                )
            
            # Store AI response
            ai_response = outputs.get("text", "")
            if ai_response:
                self.memory_service.store_memory_with_text(
                    content=ai_response,
                    memory_type="short_term",
                    session_id=self.session_id,
                    character_id=self.character_id,
                    user_id=self.user_id,
                    metadata={"sender": "dm"}
                )
    
    def clear(self) -> None:
        """Clear memory"""
        super().clear()
        # We don't clear vector DB memories as they should persist


class SummarizingMemory(VectorDBMemory):
    """Memory that periodically summarizes older conversations"""
    
    def __init__(self, *args, summarization_threshold=50, **kwargs):
        """Initialize with summarization settings"""
        super().__init__(*args, **kwargs)
        self.summarization_threshold = summarization_threshold
        self.message_count = 0
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save context and check if summarization is needed"""
        # Save to parent classes
        super().save_context(inputs, outputs)
        
        # Increment message count
        self.message_count += 1
        
        # Check if we should summarize
        if self.message_count >= self.summarization_threshold:
            self.summarize_and_prune()
            self.message_count = 0
    
    def summarize_and_prune(self) -> None:
        """Summarize older memories and prune them"""
        if not self.session_id:
            return
            
        try:
            # Check if summarization should be triggered
            from app.services.summarization_service import SummarizationService
            summarization_service = SummarizationService()
            
            # Trigger summarization
            result = summarization_service.trigger_summarization_if_needed(self.session_id)
            
            if result.get('success', False):
                logger.info(f"Summarized memories for session {self.session_id}")
                
                # Clear buffer memory (older messages have been summarized)
                # Keep a few recent messages for continuity
                recent_history = self.chat_memory.messages[-6:]  # Keep last 3 exchanges
                self.chat_memory.clear()
                for msg in recent_history:
                    self.chat_memory.add_message(msg)
        except Exception as e:
            logger.error(f"Error summarizing memories: {e}")