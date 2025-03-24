"""
Embedding Service
"""
import numpy as np
import logging
from datetime import datetime
import os
import time
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List, Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings using Hugging Face models"""
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the embedding service
        
        Args:
            model_name (str): Name of the Hugging Face model to use
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.embedding_dim = 384  # Default for all-MiniLM-L6-v2
        self.max_sequence_length = 256
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.cache = {}
        self.cache_size = 1000  # Maximum cache entries
        self.cache_hits = 0
        self.cache_misses = 0
        self.initialize_model()
    
    def initialize_model(self):
        """Load the model and tokenizer"""
        logger.info(f"Initializing embedding model: {self.model_name}")
        start_time = time.time()
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            
            # Move model to GPU if available
            self.model.to(self.device)
            
            # Set model to evaluation mode
            self.model.eval()
            
            logger.info(f"Model loaded successfully in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text string
        
        Args:
            text (str): Text to embed
            
        Returns:
            list: Vector embedding as a list of floats
        """
        # Check cache first
        if text in self.cache:
            self.cache_hits += 1
            # Move this entry to the "front" of the cache
            embedding = self.cache.pop(text)
            self.cache[text] = embedding
            return embedding
        
        self.cache_misses += 1
        
        try:
            # Prepare inputs
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_sequence_length
            )
            
            # Move inputs to the same device as the model
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate token embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Mean pooling - take the mean of all token embeddings
            token_embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask']
            
            # Expand attention mask from [batch_size, seq_length] to [batch_size, seq_length, hidden_size]
            input_mask_expanded = attention_mask.unsqueeze(-1).expand_as(token_embeddings).float()
            
            # Calculate mean of token embeddings (ignoring padding tokens)
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, dim=1)
            sum_mask = torch.clamp(attention_mask.sum(dim=1).unsqueeze(-1), min=1e-9)
            mean_pooled = sum_embeddings / sum_mask
            
            # Convert to numpy array and then to list
            embedding = mean_pooled[0].cpu().numpy().tolist()
            
            # Update cache, removing oldest entry if cache is full
            if len(self.cache) >= self.cache_size:
                self.cache.pop(next(iter(self.cache)))
            self.cache[text] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts
        
        Args:
            texts (list): List of text strings
            
        Returns:
            list: List of embeddings
        """
        if not texts:
            return []
        
        # First check cache for all texts
        results = []
        texts_to_embed = []
        indices_to_embed = []
        
        for i, text in enumerate(texts):
            if text in self.cache:
                self.cache_hits += 1
                # Get from cache and move to front
                embedding = self.cache.pop(text)
                self.cache[text] = embedding
                results.append(embedding)
            else:
                self.cache_misses += 1
                # Need to embed this text
                texts_to_embed.append(text)
                indices_to_embed.append(i)
                # Add a placeholder to results
                results.append(None)
        
        # If all texts were in cache, return results
        if not texts_to_embed:
            return results
        
        try:
            # Prepare batch inputs
            inputs = self.tokenizer(
                texts_to_embed,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.max_sequence_length
            )
            
            # Move inputs to the same device as the model
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate token embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Mean pooling
            token_embeddings = outputs.last_hidden_state
            attention_mask = inputs['attention_mask']
            input_mask_expanded = attention_mask.unsqueeze(-1).expand_as(token_embeddings).float()

            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, dim=1)
            sum_mask = torch.clamp(attention_mask.sum(dim=1).unsqueeze(-1), min=1e-9)
            batch_embeddings = sum_embeddings / sum_mask
            
            # Convert to list of lists
            batch_embeddings = batch_embeddings.cpu().numpy().tolist()
            
            # Update results and cache
            for i, idx in enumerate(indices_to_embed):
                embedding = batch_embeddings[i]
                results[idx] = embedding
                
                # Update cache
                if len(self.cache) >= self.cache_size:
                    self.cache.pop(next(iter(self.cache)))
                self.cache[texts_to_embed[i]] = embedding
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            zero_vector = [0.0] * self.embedding_dim
            for idx in indices_to_embed:
                results[idx] = zero_vector
            return results
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings"""
        return self.embedding_dim
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding cache"""
        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.cache_size,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        }