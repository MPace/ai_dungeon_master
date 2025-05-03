# app/langgraph_core/graph.py
"""
LangGraph Definition for AI Dungeon Master

This module defines the main LangGraph structure and execution flow
for the AI Dungeon Master according to the SRD.
"""
import logging
from typing import Dict, List, Any, Tuple, Callable, Optional, TypedDict
import os

from langgraph.graph import StateGraph, END
from langgraph.checkpoint import MongoDBCheckpointer

from app.langgraph_core.state import AIGameState, create_initial_game_state
from app.langgraph_core.nodes.intent_node import process_intent
from app.langgraph_core.nodes.validation_node import process_validation
from app.langgraph_core.nodes.narrative_node import process_narrative
from app.langgraph_core.nodes.ai_dm_node import process_ai_dm
from app.langgraph_core.nodes.apply_mechanics_node import process_apply_mechanics
from app.langgraph_core.nodes.memory_persistence_node import process_memory_persistence
from app.extensions import get_db

logger = logging.getLogger(__name__)

class LangGraphManager:
    """Manager class for LangGraph execution"""
    
    def __init__(self):
        """Initialize LangGraph Manager"""
        self.graph = None
        self.checkpointer = None
        self._initialize_graph()
    
    def _initialize_graph(self):
        """Initialize the LangGraph with nodes and edges"""
        try:
            # Initialize checkpointer with MongoDB
            mongo_uri = os.environ.get("MONGO_URI")
            if not mongo_uri:
                logger.error("No MongoDB URI found for checkpointer")
                return
                
            self.checkpointer = MongoDBCheckpointer(
                connection_string=mongo_uri,
                database_name="ai_dungeon_master",
                collection_name="langgraph_checkpoints"
            )
            logger.info("MongoDB checkpointer initialized for LangGraph")
            
            # Create state graph
            self.graph = StateGraph(AIGameState)
            
            # Add actual nodes from their modules
            self.graph.add_node("intent", process_intent)
            self.graph.add_node("validation", process_validation)
            self.graph.add_node("narrative", process_narrative)
            self.graph.add_node("ai_dm", process_ai_dm)
            self.graph.add_node("apply_mechanics", process_apply_mechanics)
            self.graph.add_node("memory_persistence", process_memory_persistence)
            
            # Add conditional edges
            # After intent classification, route based on intent
            self.graph.add_conditional_edges(
                "intent",
                self._route_after_intent,
                {
                    "validation": "validation",  # Go to validation for regular intents
                    "ai_dm": "ai_dm",  # Go directly to AI DM for general intents
                    "error": END  # End if intent classification failed
                }
            )
            
            # After validation, route based on validation result
            self.graph.add_conditional_edges(
                "validation",
                self._route_after_validation,
                {
                    "narrative": "narrative",  # Go to narrative update if validation passed
                    "ai_dm": "ai_dm",  # Go to AI DM even if validation failed to explain why
                    "error": END  # End if there's a critical error
                }
            )
            
            # After narrative update, go to AI DM
            self.graph.add_edge("narrative", "ai_dm")
            
            # After AI DM, go to apply mechanics
            self.graph.add_edge("ai_dm", "apply_mechanics")
            
            # After apply mechanics, go to memory persistence
            self.graph.add_edge("apply_mechanics", "memory_persistence")
            
            # After memory persistence, end
            self.graph.add_edge("memory_persistence", END)
            
            # Set the entry point
            self.graph.set_entry_point("intent")
            
            # Compile the graph
            self.graph = self.graph.compile(checkpointer=self.checkpointer)
            logger.info("LangGraph successfully compiled")
            
        except Exception as e:
            logger.error(f"Error initializing LangGraph: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.graph = None
    
    def _route_after_intent(self, state: AIGameState) -> str:
        """Route after intent classification based on the intent result"""
        intent_data = state.get("intent_data")
        
        if not intent_data or not intent_data.get("success"):
            logger.warning("Intent classification failed or not present")
            return "error"
        
        intent = intent_data.get("intent", "")
        
        # Direct certain intents straight to AI DM
        if intent in ["general", "recall", "ask_rule"]:
            logger.info(f"Routing intent '{intent}' directly to AI DM")
            return "ai_dm"
        
        # For all other intents, go to validation
        logger.info(f"Routing intent '{intent}' to validation")
        return "validation"
    
    def _route_after_validation(self, state: AIGameState) -> str:
        """Route after validation based on the validation result"""
        validation_result = state.get("validation_result")
        
        if not validation_result:
            logger.warning("Validation result not present")
            return "error"
        
        if validation_result.get("status"):
            logger.info("Validation passed, proceeding to narrative update")
            return "narrative"
        else:
            logger.warning(f"Validation failed: {validation_result.get('reason')}")
            # On validation failure, go to AI DM to explain the issue
            return "ai_dm"
    
    def process_message(self, session_id: str, message: str, 
                     character_id: Optional[str] = None, 
                     user_id: Optional[str] = None,
                     world_id: Optional[str] = None,
                     campaign_module_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a player message through the LangGraph
        
        Args:
            session_id: Session ID
            message: Player message
            character_id: Character ID
            user_id: User ID
            world_id: World ID
            campaign_module_id: Campaign module ID
        
        Returns:
            Dict[str, Any]: Processing result with DM response
        """
        if self.graph is None:
            logger.error("LangGraph not initialized")
            return {
                "success": False,
                "error": "LangGraph not initialized",
                "response": "Sorry, the AI Dungeon Master is not available right now."
            }
        
        try:
            # Check if we already have a checkpoint for this session
            has_checkpoint = self.checkpointer.get_tuple({"configurable": {"thread_id": session_id}})
            
            # Prepare initial state
            if has_checkpoint:
                # Load the existing state
                logger.info(f"Loading existing checkpoint for session {session_id}")
                state_dict = {"player_input": message}
            else:
                # Create a new initial state
                logger.info(f"Creating new initial state for session {session_id}")
                initial_state = create_initial_game_state(
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    world_id=world_id,
                    campaign_module_id=campaign_module_id
                )
                initial_state["player_input"] = message
                state_dict = initial_state
            
            # Process the message through the graph
            logger.info(f"Processing message for session {session_id}")
            result = self.graph.invoke(
                state_dict,
                config={
                    "configurable": {
                        "thread_id": session_id
                    }
                }
            )
            
            # Extract the DM response from the result
            dm_response = result.get("dm_response", "")
            
            # Log memory processing status
            if result.get("memory_processing_complete", False):
                logger.info("Memory processing completed successfully")
            else:
                logger.warning(f"Memory processing incomplete or failed: {result.get('memory_processing_error')}")
            
            # Update the session with current state info
            if has_checkpoint and result.get("current_location_id"):
                # Store any important state information in MongoDB
                db = get_db()
                if db is not None:
                    db.sessions.update_one(
                        {"session_id": session_id},
                        {"$set": {"current_location_id": result.get("current_location_id")}}
                    )
            
            return {
                "success": True,
                "response": dm_response,
                "state": result  # Include full state for debugging
            }
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, something went wrong while processing your message."
            }

# Create a singleton instance getter
def get_manager():
    """Singleton getter for the LangGraphManager"""
    if not hasattr(get_manager, "instance"):
        get_manager.instance = LangGraphManager()
    return get_manager.instance