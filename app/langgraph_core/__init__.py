# app/langgraph_core/__init__.py
"""
LangGraph Core for AI Dungeon Master

This module contains the LangGraph implementation for the AI Dungeon Master system,
including the graph definition, state management, nodes, and tools.
"""

from app.langgraph_core.graph import LangGraphManager, get_manager
from app.langgraph_core.state import (
    AIGameState,
    TrackedNarrativeState,
    EnvironmentState,
    create_initial_game_state
)

# Import for easy access
def get_orchestration_service():
    """Get the LangGraph orchestration service instance"""
    return get_manager()

__all__ = [
    # Graph components
    'LangGraphManager',
    'get_manager',
    'get_orchestration_service',
    
    # State components
    'AIGameState',
    'TrackedNarrativeState',
    'EnvironmentState',
    'create_initial_game_state'
]