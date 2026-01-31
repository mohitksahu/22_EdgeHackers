"""
Embeddings Manager - Unified interface for CLIP embeddings with caching
"""
import logging
import io
import hashlib
from typing import List, Union
from pathlib import Path
from PIL import Image

from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """
    Centralized manager for generating CLIP embeddings
    Supports: text, images (path, PIL, bytes)
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.embedder = MultimodalEmbedder()
        self._text_cache = {}
        self._cache_max_size = 1000
        self._initialized = True
        logger.info("EmbeddingsManager initialized with caching")
    
    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate CLIP embedding for text
        
        Args:
            text: Text to embed
            use_cache: Whether to use cache
            
        Returns:
            512-dimensional embedding vector
        """
        try:
            # Check cache
            if use_cache:
                text_hash = hashlib.md5(text.encode()).hexdigest()
                if text_hash in self._text_cache:
                    return self._text_cache[text_hash]
            
            # Generate embedding
            embedding = self.embedder.embed(text)
            
            # Store in cache
            if use_cache:
                if len(self._text_cache) >= self._cache_max_size:
                    first_key = next(iter(self._text_cache))
                    del self._text_cache[first_key]
                self._text_cache[text_hash] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise
    
    def embed_image(self, image: Union[str, Path, Image.Image]) -> List[float]:
        """
        Generate CLIP embedding for image
        
        Args:
            image: PIL Image or path to image file
            
        Returns:
            512-dimensional embedding vector
        """
        try:
            if isinstance(image, (str, Path)):
                image = Image.open(image)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            embedding = self.embedder.embed(image)
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed image: {e}")
            raise
    
    def embed_image_bytes(self, image_bytes: bytes) -> List[float]:
        """
        Generate CLIP embedding from image bytes
        
        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.)
            
        Returns:
            512-dimensional embedding vector
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            embedding = self.embedder.embed(image)
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed image bytes: {e}")
            raise
    
    def embed_batch_text(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Batch text embedding for efficiency"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                embeddings.append(self.embed_text(text))
        
        return embeddings
