# app/services/langchain_service.py
"""
Langchain Service
"""
import logging
import os
from typing import List, Dict, Any, Optional
from langchain.llms import BaseLLM
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from app.services.memory_service_enhanced import EnhancedMemoryService


logger = logging.getLogger(__name__)

class LangchainService:
    """Service for orchestrating AI interactions using Langchain"""
    
    def __init__(self, api_key=None, model_name="gpt-4"):
        """Initialize Langchain service with API key and model"""
        self.api_key = api_key
        self.model_name = model_name
        self.memory_service = EnhancedMemoryService()

        os.environ.pop('HTTP_PROXY', None) 
        os.environ.pop('HTTPS_PROXY', None)

        self.llm = self._create_llm()
        
    def _create_llm(self):

        try:
            if not self.api_key:
                # Get from config or environment
                from flask import current_app
                self.api_key = current_app.config.get('AI_API_KEY')
                self.model_name = current_app.config.get('AI_MODEL', )
            
            # Use OpenAI's models
            return ChatOpenAI(
                openai_api_key=self.api_key,
                model_name=self.model_name,  # This should be 'gpt-4' or similar
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"Error creating LLM: {e}")
            return None
    
    def create_dm_chain(self, system_prompt, character_data):
        """Create a chain for DM responses"""
        try:
            if not self.llm:
                logger.error("LLM not initialized")
                return None
            
            # Create prompt template
            prompt_template = f"{system_prompt}\n\n{{history}}\n\nPlayer: {{input}}\nDM:"
            
            prompt = PromptTemplate(
                input_variables=["history", "input"],
                template=prompt_template
            )
            
            # Initialize conversation memory
            memory = ConversationBufferMemory(
                memory_key="history",
                input_key="input"
            )
            
            # Create chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=memory,
                verbose=True
            )
            
            return chain
        except Exception as e:
            logger.error(f"Error creating DM chain: {e}")
            return None
    
    def create_memory_enhanced_chain(self, system_prompt, character_data, session_id):
        """Create a chain with memory enhancement"""
        try:
            if not self.llm:
                logger.error("LLM not initialized")
                return None
            
            # Create prompt template with memory context placeholder
            prompt_template = f"{system_prompt}\n\n{{memory_context}}\n\n{{history}}\n\nPlayer: {{input}}\nDM:"
            
            prompt = PromptTemplate(
                input_variables=["memory_context", "history", "input"],
                template=prompt_template
            )
            
            # Create a custom memory class that integrates with our memory service
            class EnhancedMemory(ConversationBufferMemory):
                def __init__(self, memory_service, session_id, character_id, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.memory_service = memory_service
                    self.session_id = session_id
                    self.character_id = character_id
                
                def load_memory_variables(self, inputs):
                    # Get conversation history from parent class
                    variables = super().load_memory_variables(inputs)
                    
                    # Get memory context from our memory service
                    memory_context = self.memory_service.build_memory_context(
                        current_message=inputs.get("input", ""),
                        session_id=self.session_id,
                        character_id=self.character_id
                    )
                    
                    # Add to variables
                    variables["memory_context"] = memory_context or ""
                    
                    return variables
                
                def save_context(self, inputs, outputs):
                    # Save context to parent class
                    super().save_context(inputs, outputs)
                    
                    # Store player message in our memory system
                    player_message = inputs.get("input", "")
                    self.memory_service.store_memory_with_text(
                        content=player_message,
                        session_id=self.session_id,
                        character_id=self.character_id,
                        memory_type="short_term",
                        metadata={"sender": "player"}
                    )
                    
                    # Store DM response in our memory system
                    dm_response = outputs.get("text", "")
                    self.memory_service.store_memory_with_text(
                        content=dm_response,
                        session_id=self.session_id,
                        character_id=self.character_id,
                        memory_type="short_term",
                        metadata={"sender": "dm"}
                    )
            
            # Initialize enhanced memory
            memory = EnhancedMemory(
                memory_service=self.memory_service,
                session_id=session_id,
                character_id=character_data.get("character_id"),
                memory_key="history",
                input_key="input"
            )
            
            # Create chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=memory,
                verbose=True
            )
            
            return chain
        except Exception as e:
            logger.error(f"Error creating memory-enhanced chain: {e}")
            return None
    
    def run_chain(self, chain, message, session_id=None, character_id=None):
        """Run a Langchain chain with input message"""
        try:
            if not chain:
                logger.error("Chain not initialized")
                return {"response": "Sorry, I'm having trouble thinking right now. Please try again."}
            
            # Run the chain
            response = chain.run(input=message)
            
            return {"response": response, "session_id": session_id}
        
        except Exception as e:
            logger.error(f"Error running chain: {e}")
            return {"response": f"An error occurred: {str(e)}"}