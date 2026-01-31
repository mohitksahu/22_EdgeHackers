"""
Image Processor - Handles standalone images with OCR and visual description
"""
import io
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import requests

from PIL import Image

from app.core.logging_config import get_safe_logger
from app.ingestion.processors.base_processor import BaseProcessor
from app.config import settings

logger = get_safe_logger(__name__)


class ImageProcessor(BaseProcessor):
    """Process images with OCR and visual description"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif']
    
    def process(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process image and return chunks with description"""
        file_path = Path(file_path)
        metadata = metadata or {}
        
        logger.info(f"Processing image: {file_path}")
        
        try:
            # Open and validate image
            img = Image.open(file_path)
            img_format = img.format or file_path.suffix.upper().replace('.', '')
            width, height = img.size
            mode = img.mode
            
            # Convert to RGB if necessary
            if mode not in ['RGB', 'L']:
                img = img.convert('RGB')
            
            # Get image as bytes for CLIP embedding
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            image_data = img_bytes.getvalue()
            
            # Get image description using Ollama vision or fallback
            description = self._describe_image(file_path, img)
            
            # Try OCR for text extraction
            ocr_text, ocr_confidence = self._extract_ocr_text(file_path)
            
            # Combine into content for text embedding
            content_parts = []
            if description:
                content_parts.append(f"Image description: {description}")
            if ocr_text and ocr_confidence > 30:
                content_parts.append(f"Text in image: {ocr_text}")
            
            combined_content = "\n".join(content_parts) if content_parts else f"Image: {file_path.stem}"
            
            logger.info(f"Image processed: description={bool(description)}, OCR confidence={ocr_confidence:.1f}%")
            
            # Create chunk
            chunk = {
                'chunk_id': str(uuid.uuid4()),
                'content': combined_content,
                'modality': 'image',
                'source_type': 'image',
                'chunk_index': 0,
                'total_chunks': 1,
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'processor_type': 'ImageProcessor',
                'width': width,
                'height': height,
                'format': img_format,
                'description': description,
                'ocr_text': ocr_text,
                'ocr_confidence': ocr_confidence,
                'image_data': image_data,  # For CLIP image embedding
            }
            
            return [chunk]
            
        except Exception as e:
            logger.error(f"[FAIL] Image processing failed: {e}")
            raise
    
    def _describe_image(self, file_path: Path, img: Image.Image) -> str:
        """Get image description using Ollama vision model or fallback"""
        # Try Ollama vision first
        try:
            with open(file_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Try vision-capable models
            vision_models = ['llava', 'llava:7b', 'bakllava', 'llama3.2-vision']
            
            for model in vision_models:
                try:
                    response = requests.post(
                        f"{settings.ollama_host}/api/generate",
                        json={
                            "model": model,
                            "prompt": "Describe this image in detail. Include any text, objects, people, animal, colors, and layout you observe.",
                            "images": [image_base64],
                            "stream": False
                        },
                        timeout=300  # Increased from 30 - LLaVA needs time to load initially
                    )
                    
                    if response.status_code == 200:
                        desc = response.json().get('response', '').strip()
                        if desc:
                            logger.info(f"[OK] Image described using {model}")
                            return desc
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Ollama vision failed: {e}")
        
        # Fallback to basic description
        return self._basic_description(img, file_path)
    
    def _basic_description(self, img: Image.Image, file_path: Path) -> str:
        """Generate basic description from image properties"""
        width, height = img.size
        mode = img.mode
        
        # Analyze dominant color
        try:
            img_small = img.resize((50, 50)).convert('RGB')
            colors = img_small.getcolors(maxcolors=2500)
            if colors:
                dominant = max(colors, key=lambda x: x[0])
                r, g, b = dominant[1]
                if r > 200 and g > 200 and b > 200:
                    color_name = "light/white tones"
                elif r < 50 and g < 50 and b < 50:
                    color_name = "dark/black tones"
                elif r > g and r > b:
                    color_name = "red tones"
                elif g > r and g > b:
                    color_name = "green tones"
                elif b > r and b > g:
                    color_name = "blue tones"
                else:
                    color_name = "mixed colors"
            else:
                color_name = "various colors"
        except Exception:
            color_name = "unknown colors"
        
        return f"Image '{file_path.stem}' - {width}x{height} pixels, {mode} mode, predominantly {color_name}"
    
    def _extract_ocr_text(self, file_path: Path) -> tuple:
        """Extract text from image using OCR"""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(file_path)
            
            # Get OCR text
            ocr_text = pytesseract.image_to_string(img).strip()
            
            # Get confidence
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data['conf'] if str(c).isdigit() and int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return ocr_text, avg_confidence
            
        except ImportError:
            logger.debug("pytesseract not available")
            return "", 0
        except Exception as e:
            logger.debug(f"OCR failed: {e}")
            return "", 0