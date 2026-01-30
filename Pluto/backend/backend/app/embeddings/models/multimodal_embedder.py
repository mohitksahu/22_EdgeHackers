from fastembed import ImageEmbedding, TextEmbedding
import numpy as np
from typing import List, Union
from PIL import Image
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MultimodalEmbedder:
    def __init__(self):
        # ONNX-backed CLIP models (running on CPU to save VRAM for Llama)
        cpu_provider = ["CPUExecutionProvider"]
        self.text_model = TextEmbedding(
            model_name="Qdrant/clip-ViT-B-32-text",
            providers=cpu_provider
        )
        self.image_model = ImageEmbedding(
            model_name="Qdrant/clip-ViT-B-32-vision",
            providers=cpu_provider
        )

    def encode_text(self, text: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        texts = [text] if isinstance(text, str) else text
        embeddings = list(self.text_model.embed(texts))
        return embeddings[0] if isinstance(text, str) else embeddings

    def encode_image(self, image_path: Union[str, List[str]]) -> Union[np.ndarray, List[np.ndarray]]:
        paths = [image_path] if isinstance(image_path, str) else image_path
        embeddings = list(self.image_model.embed(paths))
        return embeddings[0] if isinstance(image_path, str) else embeddings

    def embed(self, input_data: Union[str, Image.Image]) -> list:
        """
        Embed text or image into a 512D vector using fastembed.
        
        Args:
            input_data: str (text) or PIL.Image (image)
        Returns:
            list: 1D list of 512 floats
        """
        if isinstance(input_data, str):
            logger.debug(f"[fastembed] Embedding text: {input_data[:50]}...")
            embedding = self.encode_text(input_data)
            # Ensure it's a numpy array before calling tolist
            embedding_array = np.array(embedding)
            result = embedding_array.tolist()
            logger.debug(f"[fastembed] Generated text embedding: {len(result)}D")
            return result
        elif isinstance(input_data, Image.Image):
            logger.debug("[fastembed] Embedding image")
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                input_data.save(tmp.name, format='PNG')
                tmp_path = tmp.name
            try:
                embedding = self.encode_image(tmp_path)
                # Ensure it's a numpy array before calling tolist
                embedding_array = np.array(embedding)
                result = embedding_array.tolist()
                logger.debug(f"[fastembed] Generated image embedding: {len(result)}D")
                return result
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        else:
            raise ValueError("Input must be a string (text) or PIL.Image (image)")
