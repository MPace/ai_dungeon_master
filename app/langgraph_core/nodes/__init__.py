# app/langgraph_core/__init__.py

# Import manager for easy access
from app.langgraph_core.graph import LangGraphManager

# Singleton instance getter
def get_orchestration_service():
    """Get the LangGraph orchestration service instance"""
    return LangGraphManager.get_manager()