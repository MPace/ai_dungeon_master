# app/langgraph_core/tools/memory_tools.py
"""
Memory Tools for AI Dungeon Master

These tools wrap the memory services for use in the LangGraph nodes,
following the specifications in SRD section 3.4.
"""
import logging
import os
from typing import Dict, Any, List, Optional
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import numpy as np

from app.services.memory_service_enhanced import EnhancedMemoryService

logger = logging.getLogger(__name__)

class SignificanceFilterServiceTool:
    """Tool for filtering message significance using a fine-tuned DistilBERT model"""
    
    def __init__(self, model_path=None):
        """
        Initialize the significance filter with the fine-tuned DistilBERT model
        
        Args:
            model_path: Path to the fine-tuned significance classification model
        """
        self.model_path = model_path or os.environ.get("SIGNIFICANCE_MODEL_PATH", "models/significance_model")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.labels = ["not_significant", "significant"]
        self.max_seq_length = 128
        
        self._load_model()
    
    def _load_model(self):
        """Load the fine-tuned DistilBERT significance classification model"""
        try:
            logger.info(f"Loading significance classification model from {self.model_path}")
            
            # Load the tokenizer
            self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_path)
            
            # Load the model
            self.model = DistilBertForSequenceClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Significance model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading significance classification model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to load significance model: {str(e)}")
    
    def evaluate_significance(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate if a message is significant enough to store in memory
        
        Args:
            text: The message text to evaluate
            context: Additional context about the message
            
        Returns:
            Dict with significance evaluation results
        """
        try:
            if self.model is None or self.tokenizer is None:
                logger.error("Model or tokenizer not initialized")
                return {
                    "is_significant": False,
                    "importance_score": 5,
                    "confidence": 0.0,
                    "error": "Model not initialized"
                }
            
            # Tokenize the input text
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=self.max_seq_length
            )
            
            # Move inputs to the device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()[0]
                
                # Get classification result
                predicted_class_id = np.argmax(probs)
                predicted_label = self.labels[predicted_class_id]
                confidence = float(probs[predicted_class_id])
                
                # Calculate importance score (scale from 1-10)
                significance_prob = probs[1] if len(probs) > 1 else 0.0  # Probability of "significant" class
                importance_score = int(max(1, min(10, significance_prob * 10)))
            
            is_significant = predicted_label == "significant"
            
            logger.debug(f"Text significance: {is_significant} (confidence: {confidence:.2f}, importance: {importance_score})")
            
            return {
                "is_significant": is_significant,
                "importance_score": importance_score,
                "confidence": confidence,
                "classification": {
                    "label": predicted_label,
                    "probabilities": {
                        label: float(prob) for label, prob in zip(self.labels, probs)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error evaluating significance: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "is_significant": False,
                "importance_score": 5,
                "confidence": 0.0,
                "error": str(e)
            }


class StoreEpisodicMemoryTool:
    """Tool for storing episodic memories in Qdrant"""
    
    def __init__(self):
        """Initialize the episodic memory storage tool"""
        self.memory_service = EnhancedMemoryService()
    
    def store(self, content: str, session_id: str, character_id: Optional[str] = None,
              user_id: Optional[str] = None, importance: int = 5,
              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store an episodic memory in Qdrant
        
        Args:
            content: The memory content
            session_id: Session ID
            character_id: Character ID
            user_id: User ID
            importance: Importance score
            metadata: Additional metadata
            
        Returns:
            Dict with storage result
        """
        try:
            result = self.memory_service.store_memory_with_text(
                content=content,
                memory_type='episodic_event',
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata,
                async_mode=False  # Use synchronous mode for reliability
            )
            
            if result.get('success', False):
                logger.info(f"Stored episodic memory with importance {importance}")
            else:
                logger.error(f"Failed to store episodic memory: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing episodic memory: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }


class StoreSummaryMemoryTool:
    """Tool for storing summary memories in Qdrant"""
    
    def __init__(self):
        """Initialize the summary memory storage tool"""
        self.memory_service = EnhancedMemoryService()
    
    def store(self, content: str, session_id: str, character_id: Optional[str] = None,
              user_id: Optional[str] = None, importance: int = 8,
              summary_of: Optional[List[str]] = None,
              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store a summary memory in Qdrant
        
        Args:
            content: The summary content
            session_id: Session ID
            character_id: Character ID
            user_id: User ID
            importance: Importance score
            summary_of: List of memory IDs this summarizes
            metadata: Additional metadata
            
        Returns:
            Dict with storage result
        """
        try:
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'is_summary': True,
                'summary_type': 'session',
                'summarized_count': len(summary_of) if summary_of else 0,
                'summary_of': summary_of or []
            })
            
            result = self.memory_service.store_memory_with_text(
                content=content,
                memory_type='summary',
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata,
                async_mode=False  # Use synchronous mode for reliability
            )
            
            if result.get('success', False):
                logger.info(f"Stored summary memory with importance {importance}")
            else:
                logger.error(f"Failed to store summary memory: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing summary memory: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }


class StoreEntityFactTool:
    """Tool for storing entity facts in Qdrant"""
    
    def __init__(self):
        """Initialize the entity fact storage tool"""
        self.memory_service = EnhancedMemoryService()
    
    def store(self, content: str, entity_name: str, entity_type: str,
              character_id: Optional[str] = None, user_id: Optional[str] = None,
              session_id: Optional[str] = None,
              importance: int = 7, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store an entity fact in Qdrant
        
        Args:
            content: The fact content
            entity_name: Name of the entity
            entity_type: Type of entity
            character_id: Character ID
            user_id: User ID
            session_id: Session ID (optional for entity facts)
            importance: Importance score
            metadata: Additional metadata
            
        Returns:
            Dict with storage result
        """
        try:
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'entity_name': entity_name,
                'entity_type': entity_type,
                'concept_type': entity_type,  # For semantic memory interface compatibility
                'relationships': []  # Can be expanded in the future
            })
            
            result = self.memory_service.store_memory_with_text(
                content=content,
                memory_type='entity_fact',
                session_id=session_id or 'semantic',  # Use 'semantic' as default for entity facts
                character_id=character_id,
                user_id=user_id,
                importance=importance,
                metadata=metadata,
                async_mode=False  # Use synchronous mode for reliability
            )
            
            if result.get('success', False):
                logger.info(f"Stored entity fact for {entity_name} ({entity_type})")
            else:
                logger.error(f"Failed to store entity fact: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error storing entity fact: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }