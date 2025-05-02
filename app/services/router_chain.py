# app/services/router_chain.py
"""
Router Chain

This component routes player input to appropriate handlers based on intent classification.
"""
import logging
from typing import Dict, Any, Callable, List, Optional
from app.services.intent_classification_service import IntentClassificationService

logger = logging.getLogger(__name__)

class RouterChain:
    """
    Router chain that directs player input to appropriate handlers based on intent.
    As specified in the SRD, this routes based on classified intents without the 
    WorldCanonValidator component.
    """
    
    def __init__(self, intent_classifier: Optional[IntentClassificationService] = None):
        """
        Initialize router chain with intent classifier
        
        Args:
            intent_classifier: Intent classification service (created if not provided)
        """
        self.intent_classifier = intent_classifier or IntentClassificationService()
        self.validators = {}
        self.handlers = {}
        self._initialize_handlers()
    
    def _initialize_handlers(self) -> None:
        """Initialize default intent handlers"""
        # Default handler methods will be registered here
        # These will be overridden when external handlers are registered
        self.register_handler('COMBAT', self._default_combat_handler)
        self.register_handler('ACTION', self._default_action_handler)
        self.register_handler('ASK_RULE', self._default_rule_handler)
        self.register_handler('QUESTION', self._default_question_handler)
        self.register_handler('RECALL', self._default_recall_handler)
        self.register_handler('GENERAL', self._default_general_handler)
    
    def register_validator(self, intent: str, validator: Callable) -> None:
        """
        Register a validator for a specific intent
        
        Args:
            intent (str): Intent name (e.g., 'COMBAT')
            validator (Callable): Validator function
        """
        self.validators[intent] = validator
        logger.info(f"Registered validator for intent: {intent}")
    
    def register_handler(self, intent: str, handler: Callable) -> None:
        """
        Register a handler for a specific intent
        
        Args:
            intent (str): Intent name
            handler (Callable): Handler function
        """
        self.handlers[intent] = handler
        logger.info(f"Registered handler for intent: {intent}")
    
    def _default_combat_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for COMBAT intent"""
        logger.info("Using default COMBAT handler")
        return {
            'success': True,
            'message': 'Combat input processed',
            'proceed': True,  # Proceed to AI DM
            'modified_input': input_data
        }
    
    def _default_action_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for ACTION intent"""
        logger.info("Using default ACTION handler")
        return {
            'success': True,
            'message': 'Action input processed',
            'proceed': True,  # Proceed to AI DM
            'modified_input': input_data
        }
    
    def _default_rule_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for ASK_RULE intent"""
        logger.info("Using default ASK_RULE handler")
        return {
            'success': True,
            'message': 'Rule question processed',
            'proceed': True,  # Proceed to AI DM
            'modified_input': input_data
        }
    
    def _default_question_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for QUESTION intent"""
        logger.info("Using default QUESTION handler")
        return {
            'success': True,
            'message': 'Question processed',
            'proceed': True,  # Proceed to AI DM
            'modified_input': input_data
        }
    
    def _default_recall_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for RECALL intent"""
        logger.info("Using default RECALL handler")
        # For RECALL intent, we would typically retrieve memories
        # but the default handler just passes through
        return {
            'success': True,
            'message': 'Recall processed',
            'proceed': True,  # Proceed to AI DM
            'modified_input': input_data
        }
    
    def _default_general_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Default handler for GENERAL intent"""
        logger.info("Using default GENERAL handler")
        return {
            'success': True,
            'message': 'General input processed',
            'proceed': True,  # Proceed to AI DM
            'modified_input': input_data
        }
    
    def process(self, player_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process player input through the router chain
        
        Args:
            player_input (str): Player's raw text input
            context (Dict[str, Any], optional): Additional context
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            # Default context if none provided
            context = context or {}
            
            # Package input with context
            input_data = {
                'text': player_input,
                'context': context
            }
            
            # Classify intent
            classification = self.intent_classifier.classify_intent(player_input)
            
            if not classification.get('success', False):
                logger.warning("Intent classification failed, using GENERAL intent")
                intent = 'GENERAL'
            else:
                intent = classification.get('intent', 'GENERAL')
                
            logger.info(f"Classified intent: {intent} (confidence: {classification.get('confidence', 0):.4f})")
            
            # Add intent to input data
            input_data['intent'] = intent
            input_data['intent_confidence'] = classification.get('confidence', 0)
            
            # Run validator for this intent if registered
            if intent in self.validators:
                validator = self.validators[intent]
                validation_result = validator(input_data)
                
                # If validation fails, return the validation result
                if not validation_result.get('success', False):
                    logger.info(f"Validation failed for intent {intent}")
                    return validation_result
            
            # Get appropriate handler
            handler = self.handlers.get(intent, self._default_general_handler)
            
            # Process with handler
            result = handler(input_data)
            
            # Return result
            return result
            
        except Exception as e:
            logger.error(f"Error in router chain: {e}")
            
            # Return error result
            return {
                'success': False,
                'message': f"Error processing input: {str(e)}",
                'proceed': False  # Don't proceed to AI DM on error
            }
    
    def register_combat_validator(self, validator: Callable) -> None:
        """Register a validator for combat actions"""
        self.register_validator('COMBAT', validator)