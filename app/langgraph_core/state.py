# app/langgraph_core/state.py
"""
LangGraph State Object Definition

This module defines the state object used by LangGraph to manage the flow
of the AI Dungeon Master.
"""
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime

class EnvironmentState(TypedDict):
    """Environment state tracked in the narrative state"""
    current_datetime: str  # ISO 8601 format
    current_day_phase: str  # 'Morning', 'Afternoon', 'Evening', 'Night'
    area_flags: Dict[str, List[str]]  # Maps location IDs/regions to environmental flags
    # Optional fields
    season: Optional[str]
    moon_phase: Optional[str]
    global_weather: Optional[str]

class TrackedNarrativeState(TypedDict):
    """Narrative state that persists across turns"""
    quest_status: Dict[str, str]  # quest_id: current_stage_id / 'completed' / 'failed'
    npc_dispositions: Dict[str, str]  # npc_id: current_disposition_level / 'dead'
    location_states: Dict[str, Any]  # location_id: status / flags
    global_flags: List[str]  # Campaign-wide flags, including event tracking
    environment_state: EnvironmentState

class EntityReference(TypedDict):
    """Reference to an entity in memory"""
    entity_id: str
    entity_name: str
    entity_type: str

class ValidationResult(TypedDict):
    """Result of validation"""
    status: bool
    reason: Optional[str]
    details: Optional[Dict[str, Any]]

class IntentData(TypedDict):
    """Intent and slot information from the intent classifier"""
    intent: str
    slots: Dict[str, Any]
    confidence: float
    success: bool

class MemoryContext(TypedDict):
    """Memory context for the current turn"""
    history: str  # Formatted conversation history
    relevant_docs: str  # Relevant documents from vector store
    entities: str  # Entity information

class AIGameState(TypedDict):
    """Main game state object for LangGraph"""
    player_input: str
    intent_data: Optional[IntentData]
    validation_result: Optional[ValidationResult]
    dm_response: Optional[str]
    memory_context: Optional[MemoryContext]
    tracked_narrative_state: TrackedNarrativeState
    current_location_id: Optional[str]
    current_character_id: Optional[str]
    current_session_id: Optional[str]
    current_user_id: Optional[str]
    world_id: Optional[str]
    campaign_module_id: Optional[str]
    game_state: Optional[str]  # 'intro', 'exploration', 'combat', 'social', etc.
    previous_game_state: Optional[str]  # Previous game state for context

def create_initial_game_state(session_id: str, character_id: str, user_id: str, 
                            world_id: Optional[str] = None, 
                            campaign_module_id: Optional[str] = None,
                            game_state: str = 'intro') -> AIGameState:
    """
    Create the initial game state for a new session
    
    Args:
        session_id: Session ID
        character_id: Character ID
        user_id: User ID
        world_id: World ID
        campaign_module_id: Campaign module ID
        game_state: Initial game state
        
    Returns:
        AIGameState: Initial game state
    """
    # Create environment state
    environment_state: EnvironmentState = {
        'current_datetime': datetime.utcnow().isoformat(),
        'current_day_phase': 'Morning',  # Default to morning for a new game
        'area_flags': {}
    }
    
    # Create initial narrative state
    narrative_state: TrackedNarrativeState = {
        'quest_status': {},
        'npc_dispositions': {},
        'location_states': {},
        'global_flags': [],
        'environment_state': environment_state
    }
    
    # Create initial game state
    state: AIGameState = {
        'player_input': '',
        'intent_data': None,
        'validation_result': None,
        'dm_response': None,
        'memory_context': None,
        'tracked_narrative_state': narrative_state,
        'current_location_id': None,
        'current_character_id': character_id,
        'current_session_id': session_id,
        'current_user_id': user_id,
        'world_id': world_id,
        'campaign_module_id': campaign_module_id,
        'game_state': game_state,
        'previous_game_state': None
    }
    
    return state