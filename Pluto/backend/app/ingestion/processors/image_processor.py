from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
from app.ingestion.chunking.text_chunker import micro_chunk_text
"""
Image processor with OCR capabilities using Tesseract
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

import pytesseract
from PIL import Image
import cv2
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processor for image files with OCR"""

    def __init__(self):
        self.supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']

        # Configure Tesseract
        if hasattr(settings, 'TESSERACT_PATH') and settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

    def can_process(self, file_path: Path) -> bool:
        """Check if the processor can handle the file"""
        return file_path.suffix.lower() in self.supported_extensions

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results

        Args:
            image: PIL Image object

        Returns:
            Preprocessed PIL Image
        """
        # Convert to OpenCV format for processing
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Convert to grayscale for thresholding
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Apply noise reduction
        gray = cv2.medianBlur(gray, 3)

        # Apply thresholding for better contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Convert back to PIL
        processed_image = Image.fromarray(thresh)

        return processed_image

    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Dual-vector extraction for image: returns two entries (visual, OCR if confidence >70%).
        Each entry contains embedding, OCR text, resolution, and file path.
        Returns: List[Dict] with 'type' ('visual' or 'ocr'), 'embedding', 'ocr_text', 'ocr_confidence', 'metadata', 'file_path'.
        """
        try:
            logger.info(f"Processing image: {file_path}")
            image = Image.open(file_path)
            metadata = {
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'file_size': file_path.stat().st_size,
            }
            processed_image = self.preprocess_image(image)
            # OCR
            ocr_text = pytesseract.image_to_string(processed_image).strip()
            confidence_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in confidence_data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            embedder = MultimodalEmbedder()
            results = []
            
            # Visual entry (always include)
            visual_embedding = embedder.embed(image)
            results.append({
                'type': 'visual',
                'embedding': visual_embedding,
                'ocr_text': ocr_text,
                'ocr_confidence': avg_confidence,
                'metadata': metadata,
                'file_path': str(file_path),
                'chunk_index': 0,
                'total_chunks': 1  # Visual is always single chunk
            })
            
            # OCR entry (only if confidence > 70% and text is not empty)
            if avg_confidence > 70 and ocr_text:
                ocr_length = len(ocr_text)
                
                if ocr_length <= 235:
                    # Single OCR chunk
                    ocr_embedding = embedder.embed(ocr_text)
                    results.append({
                        'type': 'ocr',
                        'embedding': ocr_embedding,
                        'ocr_text': ocr_text,
                        'ocr_confidence': avg_confidence,
                        'metadata': metadata,
                        'file_path': str(file_path),
                        'chunk_index': 0,
                        'total_chunks': 1,
                        'prev_chunk_id': None,
                        'next_chunk_id': None
                    })
                    logger.info(f"Image processed: visual + 1 OCR chunk, confidence: {avg_confidence:.2f}%")
                else:
                    # Multiple OCR chunks needed
                    logger.info(f"OCR text exceeds limit ({ocr_length} chars) — splitting into chunks")
                    ocr_chunks = micro_chunk_text(ocr_text, chunk_size=235, chunk_overlap=30)
                    
                    for i, chunk_data in enumerate(ocr_chunks):
                        ocr_embedding = embedder.embed(chunk_data['chunk'])
                        results.append({
                            'type': 'ocr',
                            'embedding': ocr_embedding,
                            'ocr_text': chunk_data['chunk'],
                            'ocr_confidence': avg_confidence,
                            'metadata': metadata,
                            'file_path': str(file_path),
                            'chunk_index': i,
                            'total_chunks': len(ocr_chunks),
                            'chunk_id': chunk_data['id'],
                            'prev_chunk_id': chunk_data['prev_chunk_id'],
                            'next_chunk_id': chunk_data['next_chunk_id']
                        })
                    logger.info(f"Image processed: visual + {len(ocr_chunks)} OCR chunks, confidence: {avg_confidence:.2f}%")
            else:
                logger.info(f"Image processed: visual only (OCR confidence: {avg_confidence:.2f}%)")
            
            return results
        except Exception as e:
            logger.error(f"Failed to process image {file_path}: {e}")
            raise Exception(f"Image processing failed: {str(e)}")

    def extract_regions(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract text from different regions of the image

        Args:
            file_path: Path to the image file

        Returns:
            List of region dictionaries with text and coordinates
        """
        try:
            image = Image.open(file_path)
            processed_image = self.preprocess_image(image)

            # Get detailed OCR data
            data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)

            regions = []
            n_boxes = len(data['text'])

            for i in range(n_boxes):
                if int(data['conf'][i]) > 60:  # Only high confidence regions
                    region = {
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]),
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'source_file': str(file_path),
                        'modality': 'text',
                        'source_type': 'image'
                    }
                    regions.append(region)

            return regions

        except Exception as e:
            logger.error(f"Failed to extract regions from image {file_path}: {e}")
            return []

    def get_summary(self, file_path: Path) -> Dict[str, Any]:
        """
        Get a summary of the image without full OCR

        Args:
            file_path: Path to the image file

        Returns:
            Summary dictionary
        """
        try:
            image = Image.open(file_path)

            return {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'width': image.width,
                'height': image.height,
                'mode': image.mode,
                'format': image.format,
                'can_process': True
            }

        except Exception as e:
            logger.error(f"Failed to get image summary: {e}")
            return {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'can_process': False,
                'error': str(e)
            }