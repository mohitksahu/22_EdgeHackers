"""
CLIP Embedder for multimodal embeddings
"""
import logging
from typing import List, Union
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class CLIPEmbedder:
    """CLIP-based embedder for text and image embeddings"""

    def __init__(self):
        self.model_name = settings.clip_model_name
        
        # STRICT GPU REQUIREMENT - DO NOT FALLBACK TO CPU
        if not torch.cuda.is_available():
            errorMsg = (
                "FATAL: CUDA/GPU not available! "
                "CLIP embeddings require GPU acceleration. "
                "CPU execution is disabled for performance reasons. "
                "Please ensure CUDA is installed and a compatible GPU is available."
            )
            logger.error(errorMsg)
            raise RuntimeError(errorMsg)
        
        self.device = "cuda"
        logger.info(f"GPU detected for CLIP: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info(f"Using device: {self.device}")
        
        self.model = None
        self.processor = None
        self._load_model()

    def _load_model(self):
        """Load CLIP model and processor"""
        try:
            logger.info(f"Loading CLIP model: {self.model_name}")
            self.model = CLIPModel.from_pretrained(self.model_name, local_files_only=True).to(self.device)
            self.processor = CLIPProcessor.from_pretrained(self.model_name, local_files_only=True)
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise

    def encode_text(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode text(s) to embeddings"""
        if isinstance(texts, str):
            texts = [texts]

        try:
            inputs = self.processor(text=texts, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
                # Normalize embeddings
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            return text_features.cpu().numpy()
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise

    def encode_image(self, images: Union[Image.Image, List[Image.Image]]) -> np.ndarray:
        """Encode image(s) to embeddings"""
        if isinstance(images, Image.Image):
            images = [images]

        try:
            inputs = self.processor(images=images, return_tensors="pt").to(self.device)
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                # Normalize embeddings
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            return image_features.cpu().numpy()
        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            raise

    def encode_multimodal(self, texts: List[str], images: List[Image.Image]) -> np.ndarray:
        """Encode combined text and image for multimodal embedding"""
        try:
            # Process text
            text_inputs = self.processor(text=texts, return_tensors="pt", padding=True).to(self.device)
            # Process images
            image_inputs = self.processor(images=images, return_tensors="pt").to(self.device)

            with torch.no_grad():
                text_features = self.model.get_text_features(**text_inputs)
                image_features = self.model.get_image_features(**image_inputs)

                # Combine features (simple average for now)
                combined_features = (text_features + image_features) / 2
                # Normalize
                combined_features = combined_features / combined_features.norm(dim=-1, keepdim=True)

            return combined_features.cpu().numpy()
        except Exception as e:
            logger.error(f"Failed to encode multimodal: {e}")
            raise
