#!/usr/bin/env python3
import os
import sys
import logging
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_summarization_model():
    """Download the BART summarization model"""
    model_name = os.getenv('SUMMARIZATION_MODEL', 'facebook/bart-large-cnn')
    logger.info(f"Downloading summarization model: {model_name}")
    
    try:
        # Download the model and tokenizer
        pipeline("summarization", model=model_name)
        logger.info(f"Successfully downloaded summarization model: {model_name}")
    except Exception as e:
        logger.error(f"Error downloading summarization model: {e}")
        raise

def download_embedding_model():
    """Download the sentence transformer model for embeddings"""
    model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    logger.info(f"Downloading embedding model: {model_name}")
    
    try:
        # Download the model and tokenizer
        AutoTokenizer.from_pretrained(model_name)
        AutoModel.from_pretrained(model_name)
        logger.info(f"Successfully downloaded embedding model: {model_name}")
    except Exception as e:
        logger.error(f"Error downloading embedding model: {e}")
        raise

def main():
    """Main function to download all required models"""
    logger.info("Starting model downloads...")
    
    try:
        # Download summarization model
        download_summarization_model()
        
        # Download embedding model
        download_embedding_model()
        
        logger.info("All models downloaded successfully!")
        
    except Exception as e:
        logger.error(f"Error during model downloads: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 