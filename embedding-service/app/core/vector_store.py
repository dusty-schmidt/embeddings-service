# app/core/vector_store.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class VectorStore:
    """Qdrant vector storage manager"""
    
    def __init__(self, host: str, port: int, api_key: Optional[str] = None):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Qdrant client"""
        try:
            if self.api_key:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    api_key=self.api_key,
                    timeout=10
                )
            else:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    timeout=10
                )
            print(f"✓ Qdrant connected: {self.host}:{self.port}")
        except Exception as e:
            print(f"✗ Qdrant connection failed: {e}")
            self.client = None
    
    def ensure_collection(self, collection_name: str, vector_size: int):
        """
        Ensure collection exists, create if not
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
        """
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created Qdrant collection: {collection_name}")
            else:
                print(f"✓ Qdrant collection exists: {collection_name}")
                
        except Exception as e:
            print(f"Error ensuring collection: {e}")
            raise
    
    def insert(
        self,
        collection_name: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Insert a vector with metadata
        
        Args:
            collection_name: Collection to insert into
            text: Original text
            embedding: Vector embedding
            metadata: Additional metadata
            
        Returns:
            ID of inserted point
        """
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        point_id = str(uuid.uuid4())
        
        payload = {
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        }
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        
        self.client.upsert(
            collection_name=collection_name,
            points=[point]
        )
        
        return point_id
    
    def insert_batch(
        self,
        collection_name: str,
        texts: List[str],
        embeddings: List[List[float]],
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Insert multiple vectors at once
        
        Args:
            collection_name: Collection to insert into
            texts: List of original texts
            embeddings: List of vector embeddings
            metadata_list: List of metadata dicts (optional)
            
        Returns:
            List of inserted point IDs
        """
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        if not metadata_list:
            metadata_list = [{}] * len(texts)
        
        points = []
        point_ids = []
        
        for text, embedding, metadata in zip(texts, embeddings, metadata_list):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            
            payload = {
                "text": text,
                "timestamp": datetime.utcnow().isoformat(),
                **metadata
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        return point_ids
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            collection_name: Collection to search in
            query_vector: Query embedding
            limit: Max number of results
            score_threshold: Minimum similarity score
            filter_conditions: Metadata filters
            
        Returns:
            List of search results with scores
        """
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        # Build filter if provided
        query_filter = None
        if filter_conditions:
            conditions = []
            for key, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "text": result.payload.get("text", ""),
                "metadata": {
                    k: v for k, v in result.payload.items()
                    if k not in ["text", "timestamp"]
                }
            }
            for result in results
        ]
    
    def delete(self, collection_name: str, point_ids: List[str]):
        """Delete points by ID"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        self.client.delete(
            collection_name=collection_name,
            points_selector=point_ids
        )
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        info = self.client.get_collection(collection_name)
        
        return {
            "name": collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status
        }
    
    def is_available(self) -> bool:
        """Check if Qdrant is available"""
        if not self.client:
            return False
        
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False