import fitz  # PyMuPDF
from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
"""
PDF document processor for text extraction
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

import PyPDF2
from PyPDF2 import PdfReader

from app.config import settings

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processor for PDF documents"""

    def __init__(self):
        self.supported_extensions = ['.pdf']

    def can_process(self, file_path: Path) -> bool:
        """Check if the processor can handle the file"""
        return file_path.suffix.lower() in self.supported_extensions

    def extract_text(self, file_path: Path):
        """
        Extract text page-by-page using PyMuPDF. Returns a list of dicts with text and page_number.
        """
        try:
            logger.info(f"Processing PDF: {file_path}")
            doc = fitz.open(str(file_path))
            metadata = {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'pages': doc.page_count,
            }
            embedder = MultimodalEmbedder()
            page_chunks = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text().strip()
                if text:
                    page_chunks.append({
                        'page_number': page_num + 1,
                        'text': text,
                        'metadata': metadata,
                        'file_path': str(file_path)
                    })
            logger.info(f"PDF processed: {len(page_chunks)} non-empty pages.")
            return page_chunks
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
            raise Exception(f"PDF processing failed: {str(e)}")

    def extract_pages(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract individual pages as separate chunks

        Args:
            file_path: Path to the PDF file

        Returns:
            List of page dictionaries
        """
        result = self.extract_text(file_path)
        pages = result['pages']

        # Add source metadata to each page
        for page in pages:
            page.update({
                'source_file': str(file_path),
                'modality': 'text',
                'source_type': 'pdf',
                'metadata': result['metadata']
            })

        return pages

    def get_summary(self, file_path: Path) -> Dict[str, Any]:
        """
        Get a summary of the PDF without full text extraction

        Args:
            file_path: Path to the PDF file

        Returns:
            Summary dictionary
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)

                return {
                    'file_name': file_path.name,
                    'file_size': file_path.stat().st_size,
                    'pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.title,
                    'author': pdf_reader.metadata.author,
                    'can_process': True
                }

        except Exception as e:
            logger.error(f"Failed to get PDF summary: {e}")
            return {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'can_process': False,
                'error': str(e)
            }