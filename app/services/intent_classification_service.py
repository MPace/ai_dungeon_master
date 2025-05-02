# app/services/intent_classification_service.py
"""
Intent Classification Service

This service classifies player input intents using a fine-tuned DistilBERT model.
"""
import logging
from typing import Dict, Any, List, Tuple
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

logger = logging.getLogger(__name__)

class IntentClassificationService:
    """Service for classifying player input intents"""
    
    # Intent labels as defined in the SRD
    INTENT_LABELS = [
        'COMBAT',
        'ACTION',
        'ASK_RULE',
        'QUESTION',
        'RECALL',
        'GENERAL'
    ]
    
    def __init__(self, model_path: str = "models/intent_classifier"):
        """
        Initialize intent classification service with pre-trained DistilBERT model
        
        Args:
            model_path (str): Path to the fine-tuned model directory
        """
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.confidence_threshold = 0.8  # Threshold for classification confidence
        
        # Load the model and tokenizer
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the DistilBERT model and tokenizer"""
        try:
            logger.info(f"Loading intent classification model from {self.model_path}")
            
            # Load tokenizer
            self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_path)
            
            # Load model
            self.model = DistilBertForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            logger.info("Intent classification model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading intent classification model: {e}")
            raise
    
    def classify_intent(self, text: str) -> Dict[str, Any]:
        """
        Classify the intent of player input text
        
        Args:
            text (str): Player input text
            
        Returns:
            Dict[str, Any]: Classification result with intent label and confidence
        """
        try:
            if self.model is None or self.tokenizer is None:
                logger.error("Model or tokenizer not initialized")
                return {'intent': 'GENERAL', 'confidence': 0.0, 'success': False}
            
            # Tokenize input
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128
            ).to(self.device)
            
            # Get model output
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Get probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            probs = probs.cpu().numpy()[0]
            
            # Get predicted class
            predicted_class = int(torch.argmax(outputs.logits, dim=-1).cpu().numpy()[0])
            confidence = float(probs[predicted_class])
            
            # Get intent label
            if predicted_class < len(self.INTENT_LABELS):
                intent = self.INTENT_LABELS[predicted_class]
            else:
                logger.warning(f"Model predicted class {predicted_class} which is out of range")
                intent = "GENERAL"
            
            # If confidence is below threshold, fallback to GENERAL intent
            if confidence < self.confidence_threshold:
                logger.info(f"Low confidence ({confidence:.4f}) for intent {intent}, falling back to GENERAL")
                intent = "GENERAL"
                
            # Return classification result
            return {
                'intent': intent,
                'confidence': confidence,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return {'intent': 'GENERAL', 'confidence': 0.0, 'success': False}