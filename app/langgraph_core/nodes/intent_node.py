# app/langgraph_core/nodes/intent_node.py
"""
Intent Node for LangGraph

This node processes player input to determine intent and extract slots
using the IntentSlotFillingServiceTool.
"""
import logging
from typing import Dict, Any

from app.langgraph_core.state import AIGameState
from app.langgraph_core.tools.intent_tool import IntentSlotFillingServiceTool

logger = logging.getLogger(__name__)

class IntentNode:
    """Node for processing intent in the LangGraph"""
    
    def __init__(self):
        """Initialize intent node with the intent tool"""
        self.intent_tool = IntentSlotFillingServiceTool()
    
    def __call__(self, state: AIGameState) -> AIGameState:
        """
        Process the player input to determine intent and extract slots
        
        Args:
            state: Current state with player input
            
        Returns:
            Updated state with intent data
        """
        try:
            # Extract player input from state
            player_input = state.get("player_input", "")
            
            if not player_input:
                logger.warning("Empty player input received")
                state["intent_data"] = {
                    "intent": "general",
                    "slots": {},
                    "confidence": 0.0,
                    "success": False
                }
                return state
                
            # Call the intent tool to process the input
            logger.info(f"Processing intent for input: {player_input[:50]}...")
            intent_result = self.intent_tool.process(player_input)
            
            # Update state with intent data
            state["intent_data"] = intent_result
            
            # Log the intent result for debugging
            intent = intent_result.get("intent", "unknown")
            confidence = intent_result.get("confidence", 0.0)
            success = intent_result.get("success", False)
            
            if success:
                logger.info(f"Intent determined: {intent} (confidence: {confidence:.2f})")
                if "slots" in intent_result and intent_result["slots"]:
                    logger.info(f"Extracted slots: {intent_result['slots']}")
            else:
                logger.warning(f"Failed to determine intent. Using fallback 'general' intent.")
                # Set fallback intent
                state["intent_data"]["intent"] = "general"
                state["intent_data"]["success"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in intent node: {e}")
            # Set fallback intent on error
            state["intent_data"] = {
                "intent": "general",
                "slots": {},
                "confidence": 0.0,
                "success": True  # Still mark as success to continue the flow
            }
            return state

# Create a singleton instance
intent_node = IntentNode()

# Function to use as node in graph
def process_intent(state: AIGameState) -> AIGameState:
    """Process intent from player input"""
    return intent_node(state)