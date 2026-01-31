"""
Qdrant collection management utilities
"""
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings
from app.storage.qdrant.client import QdrantClientWrapper

logger = logging.getLogger(__name__)


def get_qdrant_client() -> QdrantClientWrapper:
    """Get Qdrant client instance"""
    return QdrantClientWrapper()


def ensure_collection_exists():
    """Ensure the collection exists with proper configuration"""
    client = get_qdrant_client()
    try:
        # Check if collection exists
        collections = client.client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if settings.collection_name not in collection_names:
            logger.info(f"Collection '{settings.collection_name}' does not exist, creating...")
            client.create_collection()
        else:
            logger.info(f"Collection '{settings.collection_name}' already exists")
    except Exception as e:
        logger.error(f"Failed to ensure collection exists: {e}")
        raise