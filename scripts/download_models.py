#!/usr/bin/env python3
import os
import sys
import logging
import shutil
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_disk_space(path):
    """Check available disk space in the given path"""
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (2**30)  # Convert to GB
    logger.info(f"Available disk space: {free_gb:.2f} GB")
    return free_gb

def download_summarization_model():
    """Download the BART summarization model"""
    model_name = os.getenv('SUMMARIZATION_MODEL', 'facebook/bart-large-cnn')
    logger.info(f"Downloading summarization model: {model_name}")
    
    try:
        # Check disk space before downloading
        cache_dir = os.getenv('TRANSFORMERS_CACHE', os.path.expanduser('~/.cache/huggingface'))
        free_space = check_disk_space(cache_dir)
        
        if free_space < 2:  # Need at least 2GB for the model
            raise RuntimeError(f"Insufficient disk space. Need at least 2GB, but only {free_space:.2f}GB available")
        
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
        # Check disk space before downloading
        cache_dir = os.getenv('TRANSFORMERS_CACHE', os.path.expanduser('~/.cache/huggingface'))
        free_space = check_disk_space(cache_dir)
        
        if free_space < 1:  # Need at least 1GB for the embedding model
            raise RuntimeError(f"Insufficient disk space. Need at least 1GB, but only {free_space:.2f}GB available")
        
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
        # Print environment information
        logger.info(f"Python version: {sys.version}")
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"Transformers cache directory: {os.getenv('TRANSFORMERS_CACHE', 'default')}")
        logger.info(f"Hugging Face home directory: {os.getenv('HF_HOME', 'default')}")
        
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