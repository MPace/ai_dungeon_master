"""
Test embedding functionality
"""
import sys
import os
import logging

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.embedding_service import EmbeddingService
from app.services.memory_service import MemoryService
from app.extensions import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_embedding_service():
    """Test the embedding service"""
    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()
        logger.info("Embedding service initialized successfully")
        
        # Test single embedding
        text = "This is a test sentence for embedding."
        embedding = embedding_service.generate_embedding(text)
        logger.info(f"Generated embedding with {len(embedding)} dimensions")
        
        # Test batch embedding
        texts = [
            "First test sentence for batch embedding.",
            "Second test sentence for batch embedding.",
            "Third test sentence for batch embedding."
        ]
        
        batch_embeddings = embedding_service.generate_batch_embeddings(texts)
        logger.info(f"Generated {len(batch_embeddings)} embeddings in batch")
        
        # Test caching
        cached_embedding = embedding_service.generate_embedding(text)
        cache_stats = embedding_service.get_cache_stats()
        logger.info(f"Cache stats: {cache_stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_memory_with_embedding():
    """Test storing and retrieving memories with embeddings"""
    try:
        # Initialize database
        init_db()
        
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Test session ID
        session_id = "test_session_123"
        
        # Store some test memories
        memories = [
            "The adventurer entered the dark cave cautiously, torch in hand.",
            "A giant dragon appeared, breathing fire and threatening the village.",
            "The hero decided to negotiate with the dragon instead of fighting.",
            "After talking, the dragon revealed it was protecting ancient treasure.",
            "The village and dragon reached a peaceful agreement to share the land."
        ]
        
        stored_memories = []
        for content in memories:
            # Generate embedding
            embedding = embedding_service.generate_embedding(content)
            
            # Store memory
            result = MemoryService.store_memory(
                session_id=session_id,
                content=content,
                embedding=embedding,
                memory_type="short_term"
            )
            
            if result['success']:
                stored_memories.append(result['memory'])
                logger.info(f"Stored memory: {content[:30]}...")
            else:
                logger.error(f"Failed to store memory: {result['error']}")
        
        # Test retrieving similar memories
        query = "The hero spoke with the dragon about a peaceful solution."
        query_embedding = embedding_service.generate_embedding(query)
        
        result = MemoryService.find_similar_memories(
            embedding=query_embedding,
            session_id=session_id,
            limit=3
        )
        
        if result['success']:
            logger.info(f"Found {len(result['memories'])} similar memories")
            for memory in result['memories']:
                logger.info(f"Similar memory: {memory.content}")
        else:
            logger.error(f"Failed to find similar memories: {result['error']}")
        
        # Test the text-based interface
        text_result = MemoryService.find_similar_memories_by_text(
            text=query,
            session_id=session_id,
            limit=3
        )
        
        if text_result['success']:
            logger.info(f"Found {len(text_result['memories'])} similar memories using text interface")
            for memory in text_result['memories']:
                logger.info(f"Similar memory (text interface): {memory.content}")
        else:
            logger.error(f"Failed to find similar memories with text: {text_result['error']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Testing embedding service...")
    if test_embedding_service():
        logger.info("Embedding service test passed!")
    else:
        logger.error("Embedding service test failed!")
    
    logger.info("\nTesting memory with embedding...")
    if test_memory_with_embedding():
        logger.info("Memory with embedding test passed!")
    else:
        logger.error("Memory with embedding test failed!")