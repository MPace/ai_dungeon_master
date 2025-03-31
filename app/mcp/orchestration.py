"""
Model Context Protocol (MCP) Orchestration Service

This module provides the central orchestration service for the Model Context Protocol,
managing the flow of context through the application.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from app.mcp.interfaces import (
    BaseContext, IContextProvider, IContextConsumer, 
    IContextTransformer, IContextOrchestrator
)
from app.mcp.context_objects import MCPContextFactory

logger = logging.getLogger(__name__)

class ContextOrchestrationService(IContextOrchestrator):
    """
    Central service for orchestrating context flow through the application.
    This service manages the registration of providers and transformers,
    and coordinates the building of context for different request types.
    """
    
    def __init__(self):
        self.providers = {}
        self.transformers = {}
        # Configuration for which providers and transformers to use for each request type
        self.request_configs = {}
        
    def register_provider(self, provider_name: str, provider: IContextProvider) -> None:
        """
        Register a context provider
        
        Args:
            provider_name: Name to register the provider under
            provider: The provider implementation
        """
        logger.info(f"Registering context provider: {provider_name}")
        self.providers[provider_name] = provider
        
    def register_transformer(self, transformer_name: str, transformer: IContextTransformer) -> None:
        """
        Register a context transformer
        
        Args:
            transformer_name: Name to register the transformer under
            transformer: The transformer implementation
        """
        logger.info(f"Registering context transformer: {transformer_name}")
        self.transformers[transformer_name] = transformer
        
    def configure_request_type(self, request_type: str, provider_names: List[str], 
                               transformer_names: List[str]) -> None:
        """
        Configure which providers and transformers to use for a request type
        
        Args:
            request_type: The type of request to configure
            provider_names: Names of providers to use for this request type
            transformer_names: Names of transformers to use for this request type
        """
        logger.info(f"Configuring request type: {request_type}")
        self.request_configs[request_type] = {
            'providers': provider_names,
            'transformers': transformer_names
        }
        
    def build_context(self, request_type: str, request_data: Dict[str, Any]) -> BaseContext:
        """
        Build context for a specific request
        
        Args:
            request_type: Type of request (e.g., 'ai_message', 'game_update')
            request_data: Data required for context building
            
        Returns:
            BaseContext: The built context
        """
        logger.info(f"Building context for request type: {request_type}")
        
        # Check if request type is configured
        if request_type not in self.request_configs:
            logger.error(f"Request type not configured: {request_type}")
            raise ValueError(f"Request type not configured: {request_type}")
        
        config = self.request_configs[request_type]
        
        # Step 1: Collect context from providers
        contexts = {}  # Store by type instead of a flat list
        for provider_name in config['providers']:
            if provider_name not in self.providers:
                logger.warning(f"Provider not found: {provider_name}")
                continue
                
            try:
                logger.debug(f"Getting context from provider: {provider_name}")
                provider = self.providers[provider_name]
                context = provider.get_context(request_data)
                # Store by context type
                context_type = context.__class__.__name__
                contexts[context_type] = context
            except Exception as e:
                logger.error(f"Error getting context from provider {provider_name}: {e}")
                # Continue with other providers
        
        if not contexts:
            logger.warning("No contexts were provided for the request")
            # Create empty AIPromptContext
            from app.mcp.context_objects import AIPromptContext
            return AIPromptContext()
        
        # Step 2: Apply transformers - without trying to merge different types
        context_list = list(contexts.values())
        
        # Find the most appropriate transformer and apply it
        for transformer_name in config['transformers']:
            if transformer_name not in self.transformers:
                logger.warning(f"Transformer not found: {transformer_name}")
                continue
                
            try:
                logger.debug(f"Applying transformer: {transformer_name}")
                transformer = self.transformers[transformer_name]
                
                # Apply transformer to each context individually
                transformed_contexts = []
                for context in context_list:
                    transformed = transformer.transform(context)
                    transformed_contexts.append(transformed)
                
                # Now all contexts should be of the same type (AIPromptContext)
                # Merge them together
                if transformed_contexts:
                    merged_context = transformed_contexts[0]
                    for context in transformed_contexts[1:]:
                        try:
                            merged_context = merged_context.merge(context)
                        except Exception as e:
                            logger.error(f"Error merging transformed contexts: {e}")
                    
                    logger.info(f"Context built successfully for request type: {request_type}")
                    return merged_context
                
            except Exception as e:
                logger.error(f"Error applying transformer {transformer_name}: {e}")
        
        # If no transformer could be applied, return the first context
        logger.warning("No transformer could be applied, returning first context")
        return next(iter(contexts.values()))
    
    def _merge_contexts(self, context1: BaseContext, context2: BaseContext) -> BaseContext:
        """
        Merge two context objects
        
        Args:
            context1: First context
            context2: Second context
            
        Returns:
            BaseContext: Merged context
        """
        return context1.merge(context2)