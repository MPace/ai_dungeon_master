# app/services/qdrant_service.py
"""
Qdrant Service

This service handles connections and operations with Qdrant vector database.
"""
import logging
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from langgraph_core.documents import Document
from qdrant_client.models import Filter, FieldCondition, MatchAny, MatchValue

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)

class QdrantService:
    """Service for handling Qdrant vector database operations"""
    
    def __init__(self, url=None, api_key=None, collection_name="memory_vectors"):
        """
        Initialize Qdrant service
        
        Args:
            url (str, optional): Qdrant Cloud URL
            api_key (str, optional): Qdrant Cloud API key
            collection_name (str, optional): Default collection name
        """
        self.url = url or os.environ.get("QDRANT_URL")
        self.api_key = api_key or os.environ.get("QDRANT_API_KEY")
        self.collection_name = collection_name
        self.client = None
        self.vector_size = 768  # Default for all-MiniLM-L6-v2
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Qdrant client"""
        try:
            if not self.url:
                logger.error("Qdrant URL not configured")
                return
                
            if not self.api_key:
                logger.error("Qdrant API key not configured")
                return
                
            self.client = QdrantClient(url=self.url, api_key=self.api_key)
            logger.info(f"Qdrant client initialized with URL: {self.url}")
            
            # Ensure the collection exists
            self._ensure_collection_exists()
            
        except Exception as e:
            logger.error(f"Error initializing Qdrant client: {e}")
            self.client = None
    
    def _ensure_collection_exists(self) -> None:
        """Ensure the collection exists, creating it if necessary"""
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return
            
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [collection.name for collection in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                # Create collection with cosine distance and vector size
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                # Create necessary payload indexes for efficient filtering
                self._create_payload_indexes()
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
    
    def _create_payload_indexes(self) -> None:
        """Create payload indexes for efficient filtering"""
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return
            
        try:
            # Create indexes for common filtering fields
            indexes = [
                ("session_id", models.PayloadSchemaType.KEYWORD),
                ("memory_type", models.PayloadSchemaType.KEYWORD),
                ("character_id", models.PayloadSchemaType.KEYWORD),
                ("user_id", models.PayloadSchemaType.KEYWORD),
                ("memory_id", models.PayloadSchemaType.KEYWORD),
                ("created_at", models.PayloadSchemaType.DATETIME),
                ("importance", models.PayloadSchemaType.INTEGER),
                # New SRD-related indexes
                ("is_summarized", models.PayloadSchemaType.BOOL),
                ("summary_id", models.PayloadSchemaType.KEYWORD),
                # Entity references would be handled through payload search, not direct indexing
            ]
            
            for field_name, field_type in indexes:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type
                )
                
            logger.info(f"Created payload indexes for collection {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error creating payload indexes: {e}")
    
    def store_vector(self, memory_id: str, embedding: List[float], payload: Dict[str, Any]) -> bool:
        """
        Store a vector in Qdrant
        
        Args:
            memory_id (str): Unique ID for the memory
            embedding (List[float]): Vector embedding
            payload (Dict[str, Any]): Associated metadata
            
        Returns:
            bool: Success status
        """
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return False
            
        try:
            # Ensure created_at is a string in ISO format for Qdrant
            if 'created_at' in payload and isinstance(payload['created_at'], datetime):
                payload['created_at'] = payload['created_at'].isoformat()
                
            if 'last_accessed' in payload and isinstance(payload['last_accessed'], datetime):
                payload['last_accessed'] = payload['last_accessed'].isoformat()
            
            # Create point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=memory_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"Vector stored with ID: {memory_id}, type: {payload.get('memory_type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing vector: {e}")
            return False
    
    
    def find_similar_vectors(self, query_vector: List[float], filters: Dict[str, Any] = None,
                           limit: int = 10, score_threshold: float = 0.7,
                           collection_name: str = None) -> List[Dict[str, Any]]:
        """
        Find vectors similar to the query vector
        
        Args:
            query_vector: The query vector to find similar vectors for
            filters: Filters to apply to the search
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score
            collection_name: Name of the collection to search
            
        Returns:
            List of similar vectors with metadata
        """
        try:
            collection_name = collection_name or self.collection_name
            
            # Build filter conditions
            filter_conditions = []
            
            if filters:
                for key, value in filters.items():
                    if key == 'memory_type' and isinstance(value, list):
                        # Handle list of memory types with MatchAny
                        filter_conditions.append(
                            FieldCondition(
                                key="memory_type",
                                match=MatchAny(any=value)
                            )
                        )
                    elif isinstance(value, list):
                        # Handle other list values
                        filter_conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchAny(any=value)
                            )
                        )
                    else:
                        # Handle single values
                        filter_conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
            
            # Create filter object
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            # Perform search
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Process results
            results = []
            for hit in search_result:
                result = {
                    'id': hit.id,
                    'score': hit.score,
                    'content': hit.payload.get('content', ''),
                    'memory_type': hit.payload.get('memory_type', ''),
                    'memory_id': hit.payload.get('memory_id', hit.id),
                    'importance': hit.payload.get('importance', 0),
                    'created_at': hit.payload.get('created_at', ''),
                    'session_id': hit.payload.get('session_id', ''),
                    'metadata': hit.payload.get('metadata', {})
                }
                
                # Add all payload fields to result
                for key, value in hit.payload.items():
                    if key not in result:
                        result[key] = value
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar vectors: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def find_similar_documents(self, query_vector: List[float], filters: Dict[str, Any] = None,
                            limit: int = 10, score_threshold: float = 0.7,
                            collection_name: str = None) -> List[Document]:
        """
        Find vectors similar to the query vector and return as LangChain Documents
        
        Args:
            query_vector: The query vector to find similar vectors for
            filters: Filters to apply to the search
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score
            collection_name: Name of the collection to search
            
        Returns:
            List of LangChain Document objects
        """
        # Get similar vectors
        results = self.find_similar_vectors(
            query_vector=query_vector,
            filters=filters,
            limit=limit,
            score_threshold=score_threshold,
            collection_name=collection_name
        )
        
        # Convert to LangChain Documents
        documents = []
        for result in results:
            # Extract content for page_content
            content = result.get('content', '')
            
            # Prepare metadata
            metadata = {
                'memory_id': result.get('memory_id', result.get('id', '')),
                'memory_type': result.get('memory_type', ''),
                'importance': result.get('importance', 0),
                'created_at': result.get('created_at', ''),
                'session_id': result.get('session_id', ''),
                'score': result.get('score', 0.0)
            }
            
            # Add additional metadata from the result
            if 'metadata' in result:
                metadata.update(result['metadata'])
            
            # Add other fields from result that aren't already in metadata
            for key, value in result.items():
                if key not in ['content', 'id', 'score'] and key not in metadata:
                    metadata[key] = value
            
            # Create Document object
            document = Document(
                page_content=content,
                metadata=metadata
            )
            documents.append(document)
        
        return documents
    
    def delete_vector(self, memory_id: str) -> bool:
        """
        Delete a vector from Qdrant
        
        Args:
            memory_id (str): ID of the vector to delete
            
        Returns:
            bool: Success status
        """
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return False
            
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[memory_id]
                )
            )
            
            logger.info(f"Vector deleted with ID: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector: {e}")
            return False
    
    def update_vector_metadata(self, memory_id: str, payload: Dict[str, Any]) -> bool:
        """
        Update vector metadata without changing the vector itself
        
        Args:
            memory_id (str): ID of the vector to update
            payload (Dict[str, Any]): New metadata
            
        Returns:
            bool: Success status
        """
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return False
            
        try:
            # Ensure datetime objects are converted to strings
            payload_copy = payload.copy()
            if 'created_at' in payload_copy and isinstance(payload_copy['created_at'], datetime):
                payload_copy['created_at'] = payload_copy['created_at'].isoformat()
                
            if 'last_accessed' in payload_copy and isinstance(payload_copy['last_accessed'], datetime):
                payload_copy['last_accessed'] = payload_copy['last_accessed'].isoformat()
            
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=payload_copy,
                points=[memory_id]
            )
            
            logger.info(f"Vector metadata updated for ID: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating vector metadata: {e}")
            return False
    
    def get_vector(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a vector by ID
        
        Args:
            memory_id (str): ID of the vector to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Vector with metadata or None if not found
        """
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return None
            
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id],
                with_vectors=True,
                with_payload=True
            )
            
            if not result:
                logger.warning(f"Vector not found with ID: {memory_id}")
                return None
                
            point = result[0]
            
            # Build result dictionary
            vector_data = {
                'memory_id': point.id,
                'embedding': point.vector
            }
            
            # Add payload data
            vector_data.update(point.payload)
            
            # Convert ISO datetime strings back to datetime objects if needed
            if 'created_at' in vector_data and isinstance(vector_data['created_at'], str):
                try:
                    vector_data['created_at'] = datetime.fromisoformat(vector_data['created_at'])
                except ValueError:
                    pass
                    
            if 'last_accessed' in vector_data and isinstance(vector_data['last_accessed'], str):
                try:
                    vector_data['last_accessed'] = datetime.fromisoformat(vector_data['last_accessed'])
                except ValueError:
                    pass
            
            logger.info(f"Vector retrieved with ID: {memory_id}")
            return vector_data
            
        except Exception as e:
            logger.error(f"Error retrieving vector: {e}")
            return None
    
    def count_vectors(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count vectors matching filters
        
        Args:
            filters (Dict[str, Any], optional): Filters to apply
            
        Returns:
            int: Count of matching vectors
        """
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return 0
            
        try:
            # Build Qdrant filter from the provided filters
            qdrant_filter = None
            if filters:
                filter_conditions = []
                
                for key, value in filters.items():
                    if value is not None:
                        # Special handling for memory_type if it's a list
                        if key == 'memory_type' and isinstance(value, list):
                            should_conditions = [
                                models.FieldCondition(
                                    key="memory_type",
                                    match=models.MatchValue(value=memory_type)
                                )
                                for memory_type in value
                            ]
                            filter_conditions.append(
                                models.Filter(should=should_conditions, should_match=1)
                            )
                        else:
                            filter_conditions.append(
                                models.FieldCondition(
                                    key=key,
                                    match=models.MatchValue(value=value)
                                )
                            )
                
                if filter_conditions:
                    qdrant_filter = models.Filter(
                        must=filter_conditions
                    )
            
            # Count vectors
            count = self.client.count(
                collection_name=self.collection_name,
                count_filter=qdrant_filter
            )
            
            logger.info(f"Counted {count.count} vectors matching filter")
            return count.count
            
        except Exception as e:
            logger.error(f"Error counting vectors: {e}")
            return 0
    
    def init_collection_for_models(self, vector_size=None):
        """
        Initialize collection with proper vector size for models
        
        Args:
            vector_size (int, optional): Size of the embedding vectors
        """
        if vector_size is not None:
            self.vector_size = vector_size
            
        # Re-initialize with updated vector size
        self._ensure_collection_exists()
    
    def find_memories_by_type(self, memory_type, session_id=None, limit=10):
        """
        Find memories by type
        
        Args:
            memory_type (str or List[str]): Memory type(s) to search for
            session_id (str, optional): Session ID to filter by
            limit (int): Maximum number of results
            
        Returns:
            List[Dict]: List of memory vectors
        """
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return []
            
        try:
            # Build filter
            filters = {}
            filters['memory_type'] = memory_type
            if session_id:
                filters['session_id'] = session_id
                
            # Create dummy vector for search (we'll sort by created_at instead of similarity)
            dummy_vector = [0.0] * self.vector_size
            
            # Use find_similar_vectors with score_threshold=0 for non-similarity-based retrieval
            results = self.find_similar_vectors(
                query_vector=dummy_vector,
                filters=filters,
                limit=limit,
                score_threshold=0.0
            )
            
            # Sort by created_at (most recent first)
            results.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding memories by type: {e}")
            return []
    
    def find_memories_with_entity(self, entity_name, session_id=None, limit=10):
        """
        Find memories that reference a specific entity
        
        Args:
            entity_name (str): Entity name to search for
            session_id (str, optional): Session ID to filter by
            limit (int): Maximum number of results
            
        Returns:
            List[Dict]: List of memory vectors
        """
        if self.client is None:
            logger.error("Qdrant client not initialized")
            return []
            
        try:
            # Build filter conditions
            filter_conditions = []
            
            # Entity reference condition - search within entity_references array
            filter_conditions.append(
                models.FieldCondition(
                    key="entity_references.entity_name",
                    match=models.MatchValue(value=entity_name)
                )
            )
            
            # Add session filter if provided
            if session_id:
                filter_conditions.append(
                    models.FieldCondition(
                        key="session_id",
                        match=models.MatchValue(value=session_id)
                    )
                )
            
            # Create filter
            qdrant_filter = models.Filter(must=filter_conditions)
            
            # Create dummy vector for search
            dummy_vector = [0.0] * self.vector_size
            
            # Scroll through results to get all matches
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=qdrant_filter,
                limit=limit,
                with_payload=True,
                with_vectors=True
            )[0]
            
            # Format results
            formatted_results = []
            for point in results:
                result = point.payload.copy()
                result['memory_id'] = point.id
                result['embedding'] = point.vector
                
                # Convert ISO datetime strings back to datetime objects
                if 'created_at' in result and isinstance(result['created_at'], str):
                    try:
                        result['created_at'] = datetime.fromisoformat(result['created_at'])
                    except ValueError:
                        pass
                
                formatted_results.append(result)
            
            # Sort by created_at (most recent first)
            formatted_results.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error finding memories with entity: {e}")
            return []