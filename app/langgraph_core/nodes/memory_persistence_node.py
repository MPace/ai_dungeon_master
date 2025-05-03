# app/langgraph_core/nodes/memory_persistence_node.py
"""
Memory Persistence Node for LangGraph

This node handles the storage of significant information from the conversation
into the memory system using Qdrant for long-term persistence.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.langgraph_core.state import AIGameState
from app.langgraph_core.tools.memory_tools import (
    SignificanceFilterServiceTool,
    StoreEpisodicMemoryTool,
    StoreSummaryMemoryTool,
    StoreEntityFactTool
)
from app.extensions import get_db

logger = logging.getLogger(__name__)

class MemoryPersistenceNode:
    """Node for persisting significant information to memory system"""
    
    def __init__(self):
        """Initialize memory persistence node with memory tools"""
        self.significance_filter = SignificanceFilterServiceTool()
        self.episodic_memory_tool = StoreEpisodicMemoryTool()
        self.summary_memory_tool = StoreSummaryMemoryTool()
        self.entity_fact_tool = StoreEntityFactTool()
        self.db = get_db()
        
        # Thresholds for triggering summarization
        self.summarization_threshold = 50  # Number of episodic memories
        self.time_window_minutes = 60  # Time window for summarization
    
    def __call__(self, state: AIGameState) -> AIGameState:
        """
        Process and store significant information from the conversation
        
        Args:
            state: Current game state with player input and DM response
            
        Returns:
            Updated state with memory processing status
        """
        try:
            # Extract necessary information from state
            player_input = state.get("player_input", "")
            dm_response = state.get("dm_response", "")
            session_id = state.get("current_session_id")
            character_id = state.get("current_character_id")
            user_id = state.get("current_user_id")
            
            if not session_id:
                logger.warning("No session ID in state, cannot persist memory")
                return state
            
            # Check significance of player input
            player_significance = self.significance_filter.evaluate_significance(
                text=player_input,
                context={
                    "sender": "player",
                    "session_id": session_id,
                    "character_id": character_id
                }
            )
            
            # Check significance of DM response
            dm_significance = self.significance_filter.evaluate_significance(
                text=dm_response,
                context={
                    "sender": "dm",
                    "session_id": session_id,
                    "character_id": character_id
                }
            )
            
            # Store player input if significant
            if player_significance["is_significant"]:
                self._store_episodic_memory(
                    content=player_input,
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    importance=player_significance["importance_score"],
                    metadata={
                        "sender": "player",
                        "classification": player_significance.get("classification", {})
                    }
                )
            
            # Store DM response if significant
            if dm_significance["is_significant"]:
                self._store_episodic_memory(
                    content=dm_response,
                    session_id=session_id,
                    character_id=character_id,
                    user_id=user_id,
                    importance=dm_significance["importance_score"],
                    metadata={
                        "sender": "dm",
                        "classification": dm_significance.get("classification", {})
                    }
                )
            
            # Extract and store entity facts from DM response
            entity_facts = self._extract_entity_facts(dm_response, state)
            for fact in entity_facts:
                self._store_entity_fact(
                    content=fact["content"],
                    entity_name=fact["entity_name"],
                    entity_type=fact["entity_type"],
                    character_id=character_id,
                    user_id=user_id,
                    session_id=session_id,
                    importance=fact.get("importance", 7),
                    metadata=fact.get("metadata", {})
                )
            
            # Check if summarization is needed
            if self._should_trigger_summarization(session_id):
                self._trigger_summarization(session_id, character_id, user_id)
            
            # Update state with memory processing status
            state["memory_processing_complete"] = True
            
            return state
            
        except Exception as e:
            logger.error(f"Error in memory persistence node: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            state["memory_processing_complete"] = False
            state["memory_processing_error"] = str(e)
            return state
    
    def _store_episodic_memory(self, content: str, session_id: str, 
                            character_id: Optional[str], user_id: Optional[str],
                            importance: int, metadata: Dict[str, Any]) -> bool:
        """
        Store an episodic memory
        
        Args:
            content: The content to store
            session_id: Session ID
            character_id: Character ID
            user_id: User ID
            importance: Importance score
            metadata: Additional metadata
            
        Returns:
            bool: Success status
        """
        try:
            result = self.episodic_memory_tool.store(
                content=content,
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata
            )
            
            if result["success"]:
                logger.info(f"Stored episodic memory with importance {importance}")
                return True
            else:
                logger.error(f"Failed to store episodic memory: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing episodic memory: {e}")
            return False
    
    def _store_entity_fact(self, content: str, entity_name: str, entity_type: str,
                        character_id: Optional[str], user_id: Optional[str],
                        session_id: str, importance: int,
                        metadata: Dict[str, Any]) -> bool:
        """
        Store an entity fact
        
        Args:
            content: The fact content
            entity_name: Name of the entity
            entity_type: Type of entity
            character_id: Character ID
            user_id: User ID
            session_id: Session ID
            importance: Importance score
            metadata: Additional metadata
            
        Returns:
            bool: Success status
        """
        try:
            result = self.entity_fact_tool.store(
                content=content,
                entity_name=entity_name,
                entity_type=entity_type,
                character_id=character_id,
                user_id=user_id,
                session_id=session_id,
                importance=importance,
                metadata=metadata
            )
            
            if result["success"]:
                logger.info(f"Stored entity fact for {entity_name} ({entity_type})")
                return True
            else:
                logger.error(f"Failed to store entity fact: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing entity fact: {e}")
            return False
    
    def _extract_entity_facts(self, dm_response: str, state: AIGameState) -> List[Dict[str, Any]]:
        """
        Extract entity facts from the DM response
        
        Args:
            dm_response: The DM's response text
            state: Current game state
            
        Returns:
            List of entity facts to store
        """
        facts = []
        
        # Extract NPC facts
        npc_facts = self._extract_npc_facts(dm_response, state)
        facts.extend(npc_facts)
        
        # Extract location facts
        location_facts = self._extract_location_facts(dm_response, state)
        facts.extend(location_facts)
        
        # Extract quest facts
        quest_facts = self._extract_quest_facts(dm_response, state)
        facts.extend(quest_facts)
        
        # Extract item facts
        item_facts = self._extract_item_facts(dm_response, state)
        facts.extend(item_facts)
        
        return facts
    
    def _extract_npc_facts(self, dm_response: str, state: AIGameState) -> List[Dict[str, Any]]:
        """Extract facts about NPCs from the DM response"""
        facts = []
        
        # Look for NPC descriptions or information
        import re
        npc_patterns = [
            r'(\w+(?:\s+\w+)?)\s+is\s+(?:a|an|the)\s+([^.!?]+)',  # "Name is a description"
            r'(?:meet|encounter|see)\s+(\w+(?:\s+\w+)?),\s+(?:a|an|the)\s+([^.!?]+)',  # "meet Name, a description"
            r'(\w+(?:\s+\w+)?)\s+(?:tells|says|explains)\s+(?:you\s+)?(?:that\s+)?([^.!?]+)',  # "Name tells you information"
        ]
        
        for pattern in npc_patterns:
            matches = re.finditer(pattern, dm_response, re.IGNORECASE)
            for match in matches:
                npc_name = match.group(1).strip()
                fact_content = match.group(2).strip()
                
                # Filter out common words that aren't likely to be NPC names
                common_words = ["you", "they", "he", "she", "it", "the", "a", "an"]
                if npc_name.lower() not in common_words and len(npc_name) > 2:
                    facts.append({
                        "content": f"{npc_name}: {fact_content}",
                        "entity_name": npc_name,
                        "entity_type": "npc",
                        "importance": 7,
                        "metadata": {
                            "source": "dm_response",
                            "extraction_type": "npc_description"
                        }
                    })
        
        return facts
    
    def _extract_location_facts(self, dm_response: str, state: AIGameState) -> List[Dict[str, Any]]:
        """Extract facts about locations from the DM response"""
        facts = []
        
        import re
        location_patterns = [
            r'(?:arrive|enter|reach)\s+(?:at|in)?\s*(?:the\s+)?([A-Z][a-zA-Z\s]+?)(?:\.|,|\s+where)',  # "arrive at Location"
            r'(?:the\s+)?([A-Z][a-zA-Z\s]+?)\s+is\s+(?:a|an)\s+([^.!?]+)',  # "Location is a description"
            r'in\s+(?:the\s+)?([A-Z][a-zA-Z\s]+?),\s+you\s+(?:see|notice|find)\s+([^.!?]+)',  # "in Location, you see..."
        ]
        
        for pattern in location_patterns:
            matches = re.finditer(pattern, dm_response)
            for match in matches:
                location_name = match.group(1).strip()
                
                # For patterns with descriptions
                if len(match.groups()) > 1:
                    fact_content = match.group(2).strip()
                    content = f"{location_name}: {fact_content}"
                else:
                    content = f"Visited {location_name}"
                
                facts.append({
                    "content": content,
                    "entity_name": location_name,
                    "entity_type": "location",
                    "importance": 6,
                    "metadata": {
                        "source": "dm_response",
                        "extraction_type": "location_description"
                    }
                })
        
        return facts
    
    def _extract_quest_facts(self, dm_response: str, state: AIGameState) -> List[Dict[str, Any]]:
        """Extract facts about quests from the DM response"""
        facts = []
        
        import re
        quest_patterns = [
            r'(?:quest|mission|task)\s+(?:to\s+)?([^.!?]+)',  # "quest to do something"
            r'(?:asks|requests|needs)\s+(?:you\s+)?(?:to\s+)?([^.!?]+)',  # "asks you to do something"
            r'(?:objective|goal):\s*([^.!?]+)',  # "objective: description"
        ]
        
        for pattern in quest_patterns:
            matches = re.finditer(pattern, dm_response, re.IGNORECASE)
            for match in matches:
                quest_content = match.group(1).strip()
                
                facts.append({
                    "content": f"Quest: {quest_content}",
                    "entity_name": "quest_objectives",
                    "entity_type": "quest",
                    "importance": 8,
                    "metadata": {
                        "source": "dm_response",
                        "extraction_type": "quest_objective"
                    }
                })
        
        return facts
    
    def _extract_item_facts(self, dm_response: str, state: AIGameState) -> List[Dict[str, Any]]:
        """Extract facts about items from the DM response"""
        facts = []
        
        import re
        item_patterns = [
            r'(?:find|discover|obtain|receive)\s+(?:a|an|the)\s+([^.!?]+)',  # "find a magical sword"
            r'(?:the\s+)?([A-Za-z\s]+?)\s+(?:is|are)\s+(?:a|an)\s+(?:magical|enchanted|cursed)\s+([^.!?]+)',  # "the sword is a magical weapon"
            r'(?:gives|hands)\s+you\s+(?:a|an|the)\s+([^.!?]+)',  # "gives you a potion"
        ]
        
        for pattern in item_patterns:
            matches = re.finditer(pattern, dm_response, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 1:
                    item_name = match.group(1).strip()
                    item_description = match.group(2).strip()
                    content = f"{item_name}: {item_description}"
                else:
                    item_name = match.group(1).strip()
                    content = f"Found: {item_name}"
                
                # Filter out overly long or nonsensical item names
                if len(item_name) < 50 and not any(word in item_name.lower() for word in ["you", "they", "he", "she"]):
                    facts.append({
                        "content": content,
                        "entity_name": item_name,
                        "entity_type": "item",
                        "importance": 6,
                        "metadata": {
                            "source": "dm_response",
                            "extraction_type": "item_description"
                        }
                    })
        
        return facts
    
    def _should_trigger_summarization(self, session_id: str) -> bool:
        """
        Check if summarization should be triggered for the session
        
        Args:
            session_id: Session ID to check
            
        Returns:
            bool: True if summarization should be triggered
        """
        try:
            # Import the memory service to check memory counts
            from app.services.memory_service_enhanced import EnhancedMemoryService
            memory_service = EnhancedMemoryService()
            
            # Check if summarization is needed
            should_summarize = memory_service.check_summarization_triggers(session_id)
            
            return should_summarize
            
        except Exception as e:
            logger.error(f"Error checking summarization triggers: {e}")
            return False
    
    def _trigger_summarization(self, session_id: str, character_id: Optional[str], user_id: Optional[str]) -> None:
        """
        Trigger summarization process for the session
        
        Args:
            session_id: Session ID
            character_id: Character ID
            user_id: User ID
        """
        try:
            logger.info(f"Triggering summarization for session {session_id}")
            
            # Get recent episodic memories for summarization
            from app.services.memory_service_enhanced import EnhancedMemoryService
            memory_service = EnhancedMemoryService()
            
            # Get unsummarized short-term memories
            from app.extensions import get_qdrant_service
            qdrant_service = get_qdrant_service()
            
            if qdrant_service is None:
                logger.error("Qdrant service not available for summarization")
                return
            
            # Query for unsummarized memories
            filters = {
                'session_id': session_id,
                'memory_type': 'short_term',
                'is_summarized': False
            }
            
            # Create a dummy vector for search (we just want to filter, not similarity search)
            dummy_vector = [0.0] * 768  # Standard embedding size
            
            memories_to_summarize = qdrant_service.find_similar_vectors(
                query_vector=dummy_vector,
                filters=filters,
                limit=50,  # Get a batch of memories
                score_threshold=0.0  # No similarity threshold since we're just filtering
            )
            
            if len(memories_to_summarize) < 10:  # Minimum threshold for summarization
                logger.info(f"Not enough memories to summarize ({len(memories_to_summarize)})")
                return
            
            # Call the summarization service
            from app.services.summarization_service import SummarizationService
            summarization_service = SummarizationService()
            
            # Extract memory IDs
            memory_ids = [m.get('memory_id') for m in memories_to_summarize if 'memory_id' in m]
            
            result = summarization_service.summarize_memories(
                session_id=session_id,
                memory_ids=memory_ids
            )
            
            if result.get('success', False):
                logger.info(f"Successfully summarized {len(memory_ids)} memories for session {session_id}")
            else:
                logger.error(f"Failed to summarize memories: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error triggering summarization: {e}")
            import traceback
            logger.error(traceback.format_exc())

# Create a singleton instance
memory_persistence_node = MemoryPersistenceNode()

# Function to use as node in graph
def process_memory_persistence(state: AIGameState) -> AIGameState:
    """Process and persist significant information to memory system"""
    return memory_persistence_node(state)