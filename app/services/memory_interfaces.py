# memory_interfaces.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

class BaseMemoryInterface(ABC):
    """Base interface for all memory types with common functionality"""
    
    @abstractmethod
    def store(self, content: str, embedding: List[float], **kwargs) -> Dict[str, Any]:
        """Store a memory entry"""
        pass
    
    @abstractmethod
    def retrieve(self, query_embedding: List[float], limit: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Retrieve memories similar to the query embedding"""
        pass
    
    @abstractmethod
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a memory entry"""
        pass
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """Delete a memory entry"""
        pass
    
    @classmethod
    def calculate_recency_score(cls, created_at: datetime) -> float:
        """Calculate a recency score based on how recent the memory is"""
        time_diff = datetime.utcnow() - created_at
        days_old = time_diff.total_seconds() / (24 * 3600)
        # Exponential decay - newer memories get higher scores
        return max(0.1, 1.0 * (0.9 ** days_old))
    
    @classmethod
    def combine_relevance_scores(cls, similarity_score: float, recency_score: float, 
                                 importance_score: float) -> float:
        """Combine different relevance factors into a single score"""
        # Default weights - can be adjusted
        similarity_weight = 0.6
        recency_weight = 0.2
        importance_weight = 0.2
        
        return (similarity_score * similarity_weight + 
                recency_score * recency_weight + 
                importance_score * importance_weight)


class ShortTermMemoryInterface(BaseMemoryInterface):
    """Interface for short-term memories that expire after a set period"""
    
    def store(self, content: str, embedding: List[float], session_id: str, 
              character_id: Optional[str] = None, user_id: Optional[str] = None,
              importance: int = 5, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a short-term memory"""
        from app.services.memory_service import MemoryService
        
        return MemoryService.store_memory(
            session_id=session_id,
            content=content,
            embedding=embedding,
            memory_type='short_term',
            character_id=character_id,
            user_id=user_id,
            importance=importance,
            metadata=metadata or {}
        )
    
    def retrieve(self, query_embedding: List[float], session_id: str, 
                 limit: int = 5, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Retrieve short-term memories similar to the query embedding"""
        from app.services.memory_service import MemoryService
        
        result = MemoryService.find_similar_memories(
            embedding=query_embedding,
            session_id=session_id,
            limit=limit,
            min_similarity=min_similarity
        )
        
        if result['success']:
            return result['memories']
        return []
    
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a short-term memory"""
        from app.extensions import get_db
        
        db = get_db()
        if db is None:
            return False
        
        try:
            result = db.memory_vectors.update_one(
                {'memory_id': memory_id, 'memory_type': 'short_term'},
                {'$set': kwargs}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a short-term memory"""
        from app.extensions import get_db
        
        db = get_db()
        if db is None:
            return False
        
        try:
            result = db.memory_vectors.delete_one(
                {'memory_id': memory_id, 'memory_type': 'short_term'}
            )
            return result.deleted_count > 0
        except Exception:
            return False


class LongTermMemoryInterface(BaseMemoryInterface):
    """Interface for long-term memories that persist indefinitely"""
    
    def store(self, content: str, embedding: List[float], session_id: str, 
              character_id: Optional[str] = None, user_id: Optional[str] = None,
              importance: int = 5, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a long-term memory"""
        from app.services.memory_service import MemoryService
        
        return MemoryService.store_memory(
            session_id=session_id,
            content=content,
            embedding=embedding,
            memory_type='long_term',
            character_id=character_id,
            user_id=user_id,
            importance=importance,
            metadata=metadata or {}
        )
    
    def retrieve(self, query_embedding: List[float], character_id: str = None, 
                 limit: int = 5, min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Retrieve long-term memories similar to the query embedding"""
        from app.extensions import get_db
        import numpy as np
        
        db = get_db()
        if db is None:
            return []
        
        try:
            query = {'memory_type': 'long_term'}
            if character_id:
                query['character_id'] = character_id
                
            # Try vector search if available
            try:
                pipeline = [
                    {
                        '$search': {
                            'index': 'vector_index',
                            'vectorSearch': {
                                'queryVector': query_embedding,
                                'path': 'embedding',
                                'numCandidates': limit * 10,
                                'limit': limit
                            }
                        }
                    },
                    {
                        '$match': query
                    },
                    {
                        '$addFields': {
                            'similarity': {
                                '$vectorDistance': ['$embedding', query_embedding, 'cosine']
                            }
                        }
                    },
                    {
                        '$match': {
                            'similarity': {'$gte': min_similarity}
                        }
                    },
                    {
                        '$sort': {
                            'similarity': -1
                        }
                    },
                    {
                        '$limit': limit
                    }
                ]
                
                return list(db.memory_vectors.aggregate(pipeline))
                
            except Exception:
                # Fallback to manual calculation
                memories = list(db.memory_vectors.find(query))
                
                # Calculate cosine similarity manually
                for memory in memories:
                    memory_embedding = memory.get('embedding', [])
                    memory['similarity'] = self._cosine_similarity(memory_embedding, query_embedding)
                
                # Filter by minimum similarity
                memories = [m for m in memories if m.get('similarity', 0) >= min_similarity]
                
                # Sort by similarity and limit results
                memories.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                return memories[:limit]
                
        except Exception:
            return []
    
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a long-term memory"""
        from app.extensions import get_db
        
        db = get_db()
        if db is None:
            return False
        
        try:
            result = db.memory_vectors.update_one(
                {'memory_id': memory_id, 'memory_type': 'long_term'},
                {'$set': kwargs}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a long-term memory"""
        from app.extensions import get_db
        
        db = get_db()
        if db is None:
            return False
        
        try:
            result = db.memory_vectors.delete_one(
                {'memory_id': memory_id, 'memory_type': 'long_term'}
            )
            return result.deleted_count > 0
        except Exception:
            return False
    
    def _cosine_similarity(self, a, b):
        """Calculate cosine similarity between two vectors"""
        if not a or not b:
            return 0
            
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0
            
        return np.dot(a, b) / (norm_a * norm_b)


class SemanticMemoryInterface(BaseMemoryInterface):
    """Interface for semantic memories (concepts, relationships, world knowledge)"""
    
    def store(self, content: str, embedding: List[float], 
              character_id: Optional[str] = None, user_id: Optional[str] = None,
              concept_type: str = 'general', relationships: Optional[List[Dict[str, str]]] = None,
              importance: int = 8, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a semantic memory"""
        from app.services.memory_service import MemoryService
        
        metadata = metadata or {}
        metadata.update({
            'concept_type': concept_type,
            'relationships': relationships or []
        })
        
        return MemoryService.store_memory(
            session_id='semantic',  # Using 'semantic' as a special constant
            content=content,
            embedding=embedding,
            memory_type='semantic',
            character_id=character_id,
            user_id=user_id,
            importance=importance,
            metadata=metadata
        )
    
    def retrieve(self, query_embedding: List[float], concept_type: Optional[str] = None,
                 character_id: Optional[str] = None, limit: int = 5, 
                 min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Retrieve semantic memories similar to the query embedding"""
        from app.extensions import get_db
        
        db = get_db()
        if db is None:
            return []
        
        try:
            query = {'memory_type': 'semantic'}
            
            if concept_type:
                query['metadata.concept_type'] = concept_type
                
            if character_id:
                query['character_id'] = character_id
                
            # Try using MongoDB's vector search if available
            try:
                pipeline = [
                    {
                        '$search': {
                            'index': 'vector_index',
                            'vectorSearch': {
                                'queryVector': query_embedding,
                                'path': 'embedding',
                                'numCandidates': limit * 10,
                                'limit': limit
                            }
                        }
                    },
                    {
                        '$match': query
                    },
                    {
                        '$addFields': {
                            'similarity': {
                                '$vectorDistance': ['$embedding', query_embedding, 'cosine']
                            }
                        }
                    },
                    {
                        '$match': {
                            'similarity': {'$gte': min_similarity}
                        }
                    },
                    {
                        '$sort': {
                            'similarity': -1
                        }
                    },
                    {
                        '$limit': limit
                    }
                ]
                
                return list(db.memory_vectors.aggregate(pipeline))
                
            except Exception:
                # Fallback to manual similarity calculation
                from app.services.memory_service import MemoryService
                memories = list(db.memory_vectors.find(query))
                
                # Calculate cosine similarity manually
                for memory in memories:
                    memory_embedding = memory.get('embedding', [])
                    memory['similarity'] = MemoryService._cosine_similarity(memory_embedding, query_embedding)
                
                # Filter by minimum similarity
                memories = [m for m in memories if m.get('similarity', 0) >= min_similarity]
                
                # Sort by similarity and limit results
                memories.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                return memories[:limit]
                
        except Exception:
            return []
    
    def update(self, memory_id: str, **kwargs) -> bool:
        """Update a semantic memory"""
        from app.extensions import get_db
        
        db = get_db()
        if db is None:
            return False
        
        try:
            result = db.memory_vectors.update_one(
                {'memory_id': memory_id, 'memory_type': 'semantic'},
                {'$set': kwargs}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a semantic memory"""
        from app.extensions import get_db
        
        db = get_db()
        if db is None:
            return False
        
        try:
            result = db.memory_vectors.delete_one(
                {'memory_id': memory_id, 'memory_type': 'semantic'}
            )
            return result.deleted_count > 0
        except Exception:
            return False