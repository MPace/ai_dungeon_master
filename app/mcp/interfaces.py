"""
Model Context Protocol (MCP) Interfaces

This module defines the core interfaces for the Model Context Protocol,
which standardizes how context is managed, transformed, and utilized
across the application, particularly for AI interactions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar

# Type variable for context objects
T = TypeVar('T', bound='BaseContext')

class BaseContext(ABC):
    """Base class for all context objects"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create context from dictionary"""
        pass
    
    @abstractmethod
    def merge(self, other: 'BaseContext') -> 'BaseContext':
        """Merge with another context object"""
        pass

class IContextProvider(ABC):
    """Interface for components that provide context"""
    
    @abstractmethod
    def get_context(self, request_data: Dict[str, Any]) -> BaseContext:
        """
        Retrieve context based on request data
        
        Args:
            request_data: Data required to retrieve the context
            
        Returns:
            BaseContext: The retrieved context
        """
        pass

class IContextConsumer(ABC):
    """Interface for components that consume context"""
    
    @abstractmethod
    def process_context(self, context: BaseContext) -> Any:
        """
        Process the provided context
        
        Args:
            context: The context to process
            
        Returns:
            Any: Result of processing the context
        """
        pass

class IContextTransformer(ABC):
    """Interface for components that transform context"""
    
    @abstractmethod
    def transform(self, context: BaseContext) -> BaseContext:
        """
        Transform the provided context
        
        Args:
            context: The context to transform
            
        Returns:
            BaseContext: The transformed context
        """
        pass

class IContextOrchestrator(ABC):
    """Interface for the context orchestration service"""
    
    @abstractmethod
    def register_provider(self, provider_name: str, provider: IContextProvider) -> None:
        """Register a context provider"""
        pass
    
    @abstractmethod
    def register_transformer(self, transformer_name: str, transformer: IContextTransformer) -> None:
        """Register a context transformer"""
        pass
    
    @abstractmethod
    def build_context(self, request_type: str, request_data: Dict[str, Any]) -> BaseContext:
        """
        Build context for a specific request
        
        Args:
            request_type: Type of request (e.g., 'ai_message', 'game_update')
            request_data: Data required for context building
            
        Returns:
            BaseContext: The built context
        """
        pass