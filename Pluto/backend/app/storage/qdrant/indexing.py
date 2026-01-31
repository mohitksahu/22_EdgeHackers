"""
Qdrant indexing utilities for multimodal embeddings
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client.http import models

from app.config import settings
from app.storage.qdrant.client import QdrantClientWrapper

logger = logging.getLogger(__name__)


class QdrantIndexer:
    """Handles indexing operations for Qdrant with Named Vectors"""

    def __init__(self):
        self.client = QdrantClientWrapper()

    def index_multimodal_document(self, document_id: str, text_embedding: List[float],
                                image_embedding: Optional[List[float]] = None,
                                audio_embedding: Optional[List[float]] = None,
                                metadata: Dict[str, Any] = None):
        """Index a document with multiple vector representations"""
        try:
            # Prepare vectors dictionary
            vectors = {
                "text_vector_space": text_embedding
            }

            if image_embedding:
                vectors["image_vector_space"] = image_embedding

            if audio_embedding:
                vectors["audio_vector"] = audio_embedding

            # Prepare payload
            payload = metadata or {}
            payload.update({
                "document_id": document_id,
                "has_text": True,
                "has_image": image_embedding is not None,
                "has_audio": audio_embedding is not None
            })

            # Create point
            point = models.PointStruct(
                id=document_id,
                vector=vectors,
                payload=payload
            )

            # Upsert point
            self.client.upsert_points([point])
            logger.info(f"Indexed document {document_id} with {len(vectors)} vectors")

        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            raise

    def batch_index_documents(self, documents: List[Dict[str, Any]]):
        """Batch index multiple documents"""
        try:
            points = []

            for doc in documents:
                document_id = doc["id"]
                text_embedding = doc["text_embedding"]
                image_embedding = doc.get("image_embedding")
                audio_embedding = doc.get("audio_embedding")
                # Support both 'metadata' and 'payload' keys from callers
                metadata = doc.get("payload") or doc.get("metadata") or {}
                
                logger.info(f"[DEBUG] Doc keys: {list(doc.keys())}")
                logger.info(f"[DEBUG] Payload from doc: {doc.get('payload')}")
                logger.info(f"[DEBUG] Metadata keys: {list(metadata.keys())}")
                logger.info(f"[DEBUG] document_topic: {metadata.get('document_topic')}")
                logger.info(f"[DEBUG] document_concepts: {metadata.get('document_concepts')}")

                # Prepare vectors dictionary
                vectors = {
                    "text_vector_space": text_embedding
                }

                if image_embedding:
                    vectors["image_vector_space"] = image_embedding

                if audio_embedding:
                    vectors["audio_vector"] = audio_embedding

                # Prepare payload
                payload = metadata.copy()
                payload.update({
                    "document_id": document_id,
                    "has_text": True,
                    "has_image": image_embedding is not None,
                    "has_audio": audio_embedding is not None
                })

                # Create point
                point = models.PointStruct(
                    id=document_id,
                    vector=vectors,
                    payload=payload
                )

                points.append(point)

            # Batch upsert
            if points:
                self.client.upsert_points(points)
                logger.info(f"Batch indexed {len(points)} documents")

        except Exception as e:
            logger.error(f"Failed to batch index documents: {e}")
            raise