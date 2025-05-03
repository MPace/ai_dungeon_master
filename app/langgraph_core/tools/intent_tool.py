# app/langgraph_core/tools/intent_tool.py
"""
Intent Slot Filling Service Tool

This tool uses a fine-tuned DistilBERT model to classify the intent of player messages
and extract relevant slots in a joint learning approach.
"""
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, DistilBertForTokenClassification
import numpy as np
import json

logger = logging.getLogger(__name__)

class IntentSlotFillingServiceTool:
    """
    Tool for intent classification and slot filling using a fine-tuned DistilBERT model.
    This implements a joint learning approach where both intent classification and 
    slot filling are performed by the same model.
    """
    
    # Supported intents from SRD 3.5
    SUPPORTED_INTENTS = [
        "cast_spell",    # Slots: {spell_name, is_ritual:boolean}
        "weapon_attack", # Slots: {weapon_name}
        "use_feature",   # Slots: {feature_name, resource}
        "use_item",      # Slots: {item_name}
        "ask_rule",      # Slots: {}
        "recall",        # Slots: {}
        "action",        # Slots: {action, skill}
        "explore",       # Slots: {sensory_type}
        "manage_item",   # Slots: {item_name, action_type}
        "rest",          # Slots: {duration} (Required: 'short' or 'long')
        "general"        # Slots: {} (Default/Fallback)
    ]
    
    def __init__(self, model_path=None):
        """
        Initialize the intent classification and slot filling tool
        
        Args:
            model_path: Path to the fine-tuned DistilBERT model
        """
        self.model_path = model_path or os.environ.get("INTENT_MODEL_PATH", "models/intent_slot_model")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.intent_model = None
        self.slot_model = None
        self.intent_labels = None
        self.slot_labels = None
        self.max_seq_length = 128  # Maximum sequence length for tokens
        
        # Load model and tokenizer
        self._load_model()
    
    def _load_model(self):
        """Load the fine-tuned DistilBERT model for intent classification and slot filling"""
        try:
            logger.info(f"Loading intent classification model from {self.model_path}")
            
            # Load the tokenizer
            self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_path)
            
            # Load the intent classification model
            self.intent_model = DistilBertForSequenceClassification.from_pretrained(
                os.path.join(self.model_path, "intent_classifier")
            )
            self.intent_model.to(self.device)
            self.intent_model.eval()
            
            # Load the slot filling model with token classification head
            self.slot_model = DistilBertForTokenClassification.from_pretrained(
                os.path.join(self.model_path, "slot_classifier")
            )
            self.slot_model.to(self.device)
            self.slot_model.eval()
            
            # Load intent and slot labels from the model directory
            with open(os.path.join(self.model_path, "intent_labels.json"), "r") as f:
                self.intent_labels = json.load(f)
            
            with open(os.path.join(self.model_path, "slot_labels.json"), "r") as f:
                self.slot_labels = json.load(f)
            
            logger.info(f"Intent classification model loaded successfully with {len(self.intent_labels)} intents")
            logger.info(f"Slot filling model loaded with {len(self.slot_labels)} slot labels")
            logger.info(f"Models are running on {self.device}")
        
        except Exception as e:
            logger.error(f"Error loading intent classification model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Failed to load DistilBERT model: {str(e)}")
    
    def process(self, text: str) -> Dict[str, Any]:
        """
        Process text to determine intent and extract slots
        
        Args:
            text: Player input text
            
        Returns:
            Dict with intent, slots, confidence, and success flag
        """
        try:
            if self.intent_model is None or self.slot_model is None or self.tokenizer is None:
                logger.error("Model or tokenizer not initialized")
                return {
                    "intent": "general",
                    "slots": {},
                    "confidence": 0.0,
                    "success": False
                }
            
            # Tokenize the input text
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding="max_length",
                truncation=True,
                max_length=self.max_seq_length,
                return_offsets_mapping=True
            )
            
            # Get the offset mapping for original text recovery
            offset_mapping = inputs.pop("offset_mapping").cpu().numpy()[0]
            
            # Move inputs to the device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Process intent classification
            with torch.no_grad():
                # Get intent classification logits
                intent_outputs = self.intent_model(**inputs)
                intent_logits = intent_outputs.logits
                
                # Convert logits to probabilities
                intent_probs = torch.nn.functional.softmax(intent_logits, dim=-1).cpu().numpy()[0]
                
                # Get the intent with highest probability
                intent_id = np.argmax(intent_probs)
                intent = self.intent_labels[intent_id]
                intent_confidence = float(intent_probs[intent_id])
                
                # Get slot filling logits from token classification model
                slot_outputs = self.slot_model(**inputs)
                slot_logits = slot_outputs.logits
                
                # Convert logits to predicted slot label indices
                slot_preds = torch.argmax(slot_logits, dim=-1).cpu().numpy()[0]
                
                # Process slot filling based on predicted BIO tags
                slots = self._extract_slots_from_bio_tags(text, intent, slot_preds, offset_mapping)
            
            logger.info(f"Classified intent: {intent} with confidence {intent_confidence:.4f}")
            logger.info(f"Extracted slots: {slots}")
            
            # Add is_ritual slot for cast_spell intent by checking the text
            if intent == "cast_spell" and "ritual" in text.lower():
                slots["is_ritual"] = True
            
            # Add default slots for specific intents if missing
            if intent == "explore" and "sensory_type" not in slots:
                slots["sensory_type"] = "visual"
                
            if intent == "rest" and "duration" not in slots:
                slots["duration"] = "short"
            
            return {
                "intent": intent,
                "slots": slots,
                "confidence": intent_confidence,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error processing intent: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "intent": "general",
                "slots": {},
                "confidence": 0.0,
                "success": False
            }
    
    def _extract_slots_from_bio_tags(self, text: str, intent: str, 
                                    slot_preds: np.ndarray, 
                                    offset_mapping: np.ndarray) -> Dict[str, Any]:
        """
        Extract slots from BIO tag predictions
        
        Args:
            text: Original text input
            intent: Classified intent
            slot_preds: Predicted slot label indices from model
            offset_mapping: Token offset mapping to original text
            
        Returns:
            Dict of extracted slot values
        """
        slots = {}
        
        # Map from slot type to expected slot names
        intent_slot_mapping = {
            "cast_spell": ["spell_name", "is_ritual"],
            "weapon_attack": ["weapon_name"],
            "use_feature": ["feature_name", "resource"],
            "use_item": ["item_name"],
            "action": ["action", "skill"],
            "explore": ["sensory_type"],
            "manage_item": ["item_name", "action_type"],
            "rest": ["duration"]
        }
        
        # Get the expected slots for this intent
        expected_slots = intent_slot_mapping.get(intent, [])
        
        # Initialize slot data structures
        current_slot_label = "O"
        current_slot_value = ""
        start_char_idx = None
        end_char_idx = None
        
        # Iterate through token predictions
        for i, (pred_idx, (start_idx, end_idx)) in enumerate(zip(slot_preds, offset_mapping)):
            # Skip special tokens and padding
            if start_idx == 0 and end_idx == 0:
                continue
                
            # Convert prediction index to slot label 
            slot_label = self.slot_labels[pred_idx]
            
            # Check if we're starting a new slot (B- tag)
            if slot_label.startswith("B-"):
                # If we were already building a slot, finalize it
                if current_slot_label != "O" and current_slot_value:
                    slot_type = current_slot_label[2:]  # Remove "B-" or "I-" prefix
                    if slot_type in expected_slots:
                        slots[slot_type] = current_slot_value.strip()
                
                # Start a new slot
                current_slot_label = slot_label
                slot_type = slot_label[2:]  # Remove "B-" prefix
                
                # Get the token text from the original string
                if start_idx < len(text) and end_idx <= len(text):
                    current_slot_value = text[start_idx:end_idx]
                    start_char_idx = start_idx
                    end_char_idx = end_idx
                else:
                    current_slot_value = ""
                    start_char_idx = None
                    end_char_idx = None
            
            # Continue an existing slot (I- tag)
            elif slot_label.startswith("I-") and current_slot_label != "O":
                # Check if this I- tag matches the current slot type
                current_type = current_slot_label[2:]
                this_type = slot_label[2:]
                
                if current_type == this_type and end_idx > 0:
                    # Append the token text to the current slot value
                    if end_idx <= len(text):
                        current_slot_value += text[start_idx:end_idx]
                        end_char_idx = end_idx
            
            # Outside tag - finish any current slot
            elif slot_label == "O" and current_slot_label != "O":
                # Finalize the current slot
                slot_type = current_slot_label[2:]  # Remove "B-" or "I-" prefix
                if slot_type in expected_slots and current_slot_value:
                    slots[slot_type] = current_slot_value.strip()
                
                # Reset for the next slot
                current_slot_label = "O"
                current_slot_value = ""
                start_char_idx = None
                end_char_idx = None
        
        # Handle any final slot that hasn't been processed yet
        if current_slot_label != "O" and current_slot_value:
            slot_type = current_slot_label[2:]  # Remove "B-" or "I-" prefix
            if slot_type in expected_slots:
                slots[slot_type] = current_slot_value.strip()
        
        # Post-process slots for specific intents
        if intent == "rest" and "duration" in slots:
            # Ensure duration is either "short" or "long"
            duration = slots["duration"].lower()
            if "long" in duration:
                slots["duration"] = "long"
            else:
                slots["duration"] = "short"
        
        # For boolean slots like is_ritual, convert to boolean
        if intent == "cast_spell" and "is_ritual" in slots:
            slots["is_ritual"] = slots["is_ritual"].lower() in ["true", "yes", "ritual"]
        
        return slots