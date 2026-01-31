"""
Qdrant client for vector storage with Named Vectors architecture
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
import requests

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantClientWrapper:
    """Qdrant client with connection pooling"""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        """Singleton pattern for connection reuse"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=30.0,
                prefer_grpc=False  # Use HTTP for better compatibility
            )
            logger.info("Qdrant client initialized")
    
    @property
    def client(self):
        """Get the shared client instance"""
        return self._client
    
    def health_check(self) -> bool:
        """Check Qdrant connection health"""
        try:
            self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def create_collection(self):
        """Create collection with Named Vectors for multimodal support"""
        try:
            # Define vector configurations for different modalities
            vectors_config = {
                "text_vector_space": models.VectorParams(
                    size=settings.embedding_dimension,
                    distance=models.Distance.COSINE
                ),
                "image_vector_space": models.VectorParams(
                    size=settings.embedding_dimension,
                    distance=models.Distance.COSINE
                ),
                "audio_vector": models.VectorParams(
                    size=settings.embedding_dimension,
                    distance=models.Distance.COSINE
                )
            }

            self.client.recreate_collection(
                collection_name=settings.collection_name,
                vectors_config=vectors_config
            )
            logger.info(f"Created collection '{settings.collection_name}' with Named Vectors")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise

    def get_collection(self):
        """Get collection info"""
        try:
            return self.client.get_collection(collection_name=settings.collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection: {e}")
            raise

    def get_points_count(self) -> int:
        """Get the total number of points in the collection"""
        try:
            collection_info = self.get_collection()
            return collection_info.points_count
        except Exception as e:
            logger.error(f"Failed to get points count: {e}")
            return 0

    def upsert_points(self, points: List[models.PointStruct]):
        """Upsert points with Named Vectors"""
        try:
            self.client.upsert(
                collection_name=settings.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} points to collection")
        except Exception as e:
            logger.error(f"Failed to upsert points: {e}")
            raise

    def search_vectors(self, query_vector: List[float], vector_name: str, limit: int = 10,
                      score_threshold: float = 0.4, filter_conditions: Optional[models.Filter] = None) -> List[models.ScoredPoint]:
        """Search vectors with Named Vectors and filtering"""
        try:
            search_result = self.client.query_points(
                collection_name=settings.collection_name,
                query=query_vector,
                using=vector_name,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions
            )
            return search_result.points
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise

    def delete_points(self, point_ids: List[str]):
        """Delete points by IDs"""
        try:
            self.client.delete(
                collection_name=settings.collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            logger.info(f"Deleted {len(point_ids)} points")
        except Exception as e:
            logger.error(f"Failed to delete points: {e}")
            raise

    def delete_collection(self):
        """Delete the entire collection"""
        try:
            self.client.delete_collection(collection_name=settings.collection_name)
            logger.info(f"Deleted collection '{settings.collection_name}'")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise

    def scroll_all_points(self, limit: int = 10000) -> List[models.Record]:
        """Scroll through all points in collection"""
        try:
            scroll_result = self.client.scroll(
                collection_name=settings.collection_name,
                limit=limit,
                with_payload=True
            )
            return scroll_result[0]  # Return points, ignore next_page_offset
        except Exception as e:
            logger.error(f"Failed to scroll all points: {e}")
            return []

    def scroll_points(self, filter_conditions: Optional[models.Filter] = None, limit: int = 1000) -> List[models.Record]:
        """Scroll through points with optional filtering"""
        try:
            scroll_result = self.client.scroll(
                collection_name=settings.collection_name,
                scroll_filter=filter_conditions,
                limit=limit,
                with_payload=True
            )
            return scroll_result[0]  # Return points, ignore next_page_offset
        except Exception as e:
            logger.error(f"Failed to scroll points: {e}")
            return []