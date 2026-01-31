"""
PDF Processor - Extract BOTH text AND images from PDFs
- Images are saved to data/extracted_images/
- Images are described using vision model
- Text and images get CLIP embeddings
- Metadata links content to source PDF and page
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


class PDFProcessor(BaseProcessor):
    """
    Process PDFs extracting both text and images
    
    Features:
    - Extracts text from each page
    - Extracts images from each page and saves them
    - Describes images using vision model
    - Creates chunks with proper metadata linking to source
    """
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.pdf']
        
        # Directory to save extracted images
        self.extracted_images_dir = settings.data_dir / "extracted_images"
        self.extracted_images_dir.mkdir(parents=True, exist_ok=True)
        
        self.min_image_size = 50  # Minimum dimension to extract (skip icons)
        self.chunk_size = 512
        self.chunk_overlap = 50
    
    def process(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process PDF extracting both text and images
        
        Returns:
            List of chunks including:
            - Text chunks (from each page)
            - Image chunks (with descriptions)
        """
        file_path = Path(file_path)
        metadata = metadata or {}
        
        logger.info(f"[PDF] Processing: {file_path.name}")
        
        all_chunks = []
        pdf_id = str(uuid.uuid4())[:8]  # Unique ID for this PDF
        
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            logger.info(f"[PDF] Document has {total_pages} pages")
            
            text_chunk_count = 0
            image_chunk_count = 0
            
            # Process each page
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Common metadata for this page
                page_metadata = {
                    'pdf_id': pdf_id,
                    'page_number': page_num + 1,
                    'total_pages': total_pages,
                    'source_pdf': file_path.name,
                    'source_pdf_path': str(file_path),
                }
                
                # 1. Extract TEXT from page
                text_chunks = self._extract_page_text(
                    page, page_num, file_path, page_metadata
                )
                all_chunks.extend(text_chunks)
                text_chunk_count += len(text_chunks)
                
                # 2. Extract IMAGES from page
                image_chunks = self._extract_page_images(
                    doc, page, page_num, file_path, page_metadata, pdf_id
                )
                all_chunks.extend(image_chunks)
                image_chunk_count += len(image_chunks)
            
            doc.close()
            
            # Update chunk indices
            for i, chunk in enumerate(all_chunks):
                chunk['chunk_index'] = i
                chunk['total_chunks'] = len(all_chunks)
            
            logger.info(f"[PDF] Extracted {text_chunk_count} text chunks + {image_chunk_count} image chunks")
            
            return all_chunks
            
        except ImportError:
            logger.error("[FAIL] PyMuPDF (fitz) not installed. Run: pip install pymupdf")
            raise
        except Exception as e:
            logger.error(f"[FAIL] PDF processing failed: {e}")
            raise
    
    def _extract_page_text(
        self,
        page,
        page_num: int,
        file_path: Path,
        page_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract and chunk text from a single page"""
        chunks = []
        
        # Get text from page
        text = page.get_text("text")
        if not text or len(text.strip()) < 20:
            return chunks
        
        # Clean text
        text = self._clean_text(text)
        
        # Chunk if needed
        if len(text) <= self.chunk_size:
            chunks.append({
                'chunk_id': str(uuid.uuid4()),
                'content': text,
                'modality': 'text',
                'source_type': 'pdf_text',
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'processor_type': 'PDFProcessor',
                **page_metadata,
            })
        else:
            # Split long text
            words = text.split()
            current = []
            current_len = 0
            
            for word in words:
                if current_len + len(word) > self.chunk_size and current:
                    chunk_text = ' '.join(current)
                    chunks.append({
                        'chunk_id': str(uuid.uuid4()),
                        'content': chunk_text,
                        'modality': 'text',
                        'source_type': 'pdf_text',
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'file_size': file_path.stat().st_size,
                        'processor_type': 'PDFProcessor',
                        **page_metadata,
                    })
                    # Keep overlap
                    current = current[-10:] if len(current) > 10 else []
                    current_len = sum(len(w) for w in current)
                
                current.append(word)
                current_len += len(word) + 1
            
            if current:
                chunk_text = ' '.join(current)
                chunks.append({
                    'chunk_id': str(uuid.uuid4()),
                    'content': chunk_text,
                    'modality': 'text',
                    'source_type': 'pdf_text',
                    'file_name': file_path.name,
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'processor_type': 'PDFProcessor',
                    **page_metadata,
                })
        
        return chunks
    
    def _extract_page_images(
        self,
        doc,
        page,
        page_num: int,
        file_path: Path,
        page_metadata: Dict[str, Any],
        pdf_id: str
    ) -> List[Dict[str, Any]]:
        """Extract images from page, save them, and create chunks"""
        chunks = []
        
        try:
            image_list = page.get_images(full=True)
            
            for img_idx, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    
                    if not base_image:
                        continue
                    
                    image_bytes = base_image["image"]
                    image_ext = base_image.get("ext", "png")
                    
                    # Load image
                    img = Image.open(io.BytesIO(image_bytes))
                    width, height = img.size
                    
                    # Skip small images (likely icons/bullets)
                    if width < self.min_image_size or height < self.min_image_size:
                        continue
                    
                    # Save extracted image to disk
                    image_filename = f"{pdf_id}_page{page_num + 1}_img{img_idx + 1}.{image_ext}"
                    image_save_path = self.extracted_images_dir / image_filename
                    
                    with open(image_save_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    logger.info(f"[PDF] Saved image: {image_filename} ({width}x{height})")
                    
                    # Get image description
                    description = self._describe_image(image_save_path)
                    
                    # Prepare image data for CLIP embedding
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    image_data = img_buffer.getvalue()
                    
                    # Create content for text embedding
                    content = f"Image from {file_path.name} page {page_num + 1}: {description}"
                    
                    # Create chunk
                    chunk = {
                        'chunk_id': str(uuid.uuid4()),
                        'content': content,
                        'modality': 'image',
                        'source_type': 'pdf_image',
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'file_size': file_path.stat().st_size,
                        'processor_type': 'PDFProcessor',
                        'image_path': str(image_save_path),
                        'image_filename': image_filename,
                        'image_index': img_idx + 1,
                        'width': width,
                        'height': height,
                        'description': description,
                        'image_data': image_data,  # For CLIP image embedding
                        **page_metadata,
                    }
                    
                    chunks.append(chunk)
                    
                except Exception as e:
                    logger.warning(f"[WARN] Failed to extract image {img_idx} from page {page_num}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"[WARN] Image extraction failed for page {page_num}: {e}")
        
        return chunks
    
    def _describe_image(self, image_path: Path) -> str:
        """Describe image using Ollama vision model"""
        try:
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Try vision models
            vision_models = ['llava', 'llava:7b', 'bakllava']
            
            for model in vision_models:
                try:
                    response = requests.post(
                        f"{settings.ollama_host}/api/generate",
                        json={
                            "model": model,
                            "prompt": "Describe this image concisely in 1-2 sentences. Focus on the main content and any visible text.",
                            "images": [image_base64],
                            "stream": False,
                            "options": {"temperature": 0.3, "num_predict": 100}
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        desc = response.json().get('response', '').strip()
                        if desc:
                            return desc
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Vision description failed: {e}")
        
        # Fallback
        return f"Image extracted from PDF ({image_path.stem})"
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        import re
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()