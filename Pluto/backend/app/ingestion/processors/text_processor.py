"""
Text Processor - Handles plain text files (.txt, .md, .html, etc.)
NOTE: PDFs are handled by PDFProcessor, not this processor
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

from app.core.logging_config import get_safe_logger
from app.ingestion.processors.base_processor import BaseProcessor
from app.config import settings

logger = get_safe_logger(__name__)


class TextProcessor(BaseProcessor):
    """Process plain text files"""
    
    def __init__(self):
        super().__init__()
        # NOTE: .pdf is NOT included - PDFProcessor handles PDFs
        self.supported_extensions = ['.txt', '.md', '.html', '.json', '.csv', '.xml']
        self.chunk_size = 512
        self.chunk_overlap = 50
    
    def process(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process text file and return chunks"""
        file_path = Path(file_path)
        metadata = metadata or {}
        
        logger.info(f"Processing text file: {file_path}")
        
        try:
            # Read text content
            text = self._read_text_file(file_path)
            
            if not text or len(text.strip()) < 10:
                logger.warning(f"No text content extracted from {file_path.name}")
                return []
            
            # Clean text
            text = self._clean_text(text)
            
            # Create chunks
            chunks = self._create_chunks(text, file_path, metadata)
            
            logger.info(f"Successfully processed text file: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"[FAIL] Text processing failed: {e}")
            raise
    
    def _read_text_file(self, file_path: Path) -> str:
        """Read plain text file with encoding detection"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Binary fallback
        return file_path.read_bytes().decode('utf-8', errors='ignore')
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def _create_chunks(
        self,
        text: str,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create overlapping chunks from text"""
        chunks = []
        
        # If text is short enough, return as single chunk
        if len(text) <= self.chunk_size:
            chunks.append({
                'chunk_id': str(uuid.uuid4()),
                'content': text,
                'modality': 'text',
                'source_type': 'text',
                'chunk_index': 0,
                'total_chunks': 1,
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'processor_type': 'TextProcessor',
            })
            return chunks
        
        # Split into sentences for better chunking
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': str(uuid.uuid4()),
                    'content': chunk_text,
                    'modality': 'text',
                    'source_type': 'text',
                    'chunk_index': chunk_index,
                    'file_name': file_path.name,
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'processor_type': 'TextProcessor',
                })
                
                # Keep overlap
                overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else ""
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text)
                chunk_index += 1
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': str(uuid.uuid4()),
                'content': chunk_text,
                'modality': 'text',
                'source_type': 'text',
                'chunk_index': chunk_index,
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'processor_type': 'TextProcessor',
            })
        
        # Update total chunks
        total = len(chunks)
        for chunk in chunks:
            chunk['total_chunks'] = total
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]