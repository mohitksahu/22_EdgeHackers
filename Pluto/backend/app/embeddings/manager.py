"""
Embeddings Manager - Unified interface for multimodal embeddings
"""
import logging
from typing import List, Union, Dict, Any
from pathlib import Path
from PIL import Image
import numpy as np

from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """Centralized manager for generating embeddings across modalities"""

    def __init__(self):
        self.embedder = MultimodalEmbedder()
        logger.info("EmbeddingsManager initialized")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Input text string
            
        Returns:
            List of floats representing the embedding
        """
        try:
            embedding = self.embedder.embed(text)
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise

    def embed_image(self, image: Union[str, Path, Image.Image]) -> List[float]:
        """
        Generate embedding for image
        
        Args:
            image: PIL Image, or path to image file
            
        Returns:
            List of floats representing the embedding
        """
        try:
            if isinstance(image, (str, Path)):
                image = Image.open(image)
            
            embedding = self.embedder.embed(image)
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed image: {e}")
            raise

    def embed_batch_text(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embeddings
        """
        embeddings = []
        for text in texts:
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed text in batch: {e}")
                # Add zero vector on failure to maintain batch consistency
                embeddings.append([0.0] * 512)
        
        return embeddings

    def embed_batch_images(self, images: List[Union[str, Path, Image.Image]]) -> List[List[float]]:
        """
        Generate embeddings for multiple images
        
        Args:
            images: List of PIL Images or paths
            
        Returns:
            List of embeddings
        """
        embeddings = []
        for image in images:
            try:
                embedding = self.embed_image(image)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed image in batch: {e}")
                embeddings.append([0.0] * 512)
        
        return embeddings

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add embeddings to text chunks
        
        Args:
            chunks: List of chunk dictionaries with 'content' field
            
        Returns:
            Chunks with added 'embedding' field
        """
        for chunk in chunks:
            try:
                content = chunk.get('content', chunk.get('text', ''))
                if content:
                    chunk['embedding'] = self.embed_text(content)
                else:
                    logger.warning(f"Empty content in chunk: {chunk.get('chunk_id', 'unknown')}")
                    chunk['embedding'] = [0.0] * 512
            except Exception as e:
                logger.error(f"Failed to embed chunk: {e}")
                chunk['embedding'] = [0.0] * 512
        
        return chunks

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return 512  # CLIP embeddings are 512-dimensional
