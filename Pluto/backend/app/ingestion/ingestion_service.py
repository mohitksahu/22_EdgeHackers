"""
Ingestion service for processing various document types
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.ingestion.processors.pdf_processor import PDFProcessor
from app.ingestion.processors.image_processor import ImageProcessor
from app.ingestion.processors.audio_processor import AudioProcessor
from app.ingestion.processors.text_processor import TextProcessor
from app.ingestion.chunking.text_chunker import micro_chunk_text
from app.config import settings

logger = logging.getLogger(__name__)



def get_chunker(chunking_strategy: str, chunk_size: int = 235, overlap: int = 30):
    """Return a chunker function based on strategy. Only 'character' is supported for now."""
    from app.ingestion.chunking.text_chunker import micro_chunk_text
    class CharacterChunker:
        def chunk_text(self, text, metadata=None):
            raw_chunks = micro_chunk_text(text, chunk_size=chunk_size, chunk_overlap=overlap)
            # Add metadata to each chunk
            for chunk in raw_chunks:
                if metadata:
                    chunk.update(metadata)
                # Ensure required fields are present
                chunk.setdefault('content', chunk.get('chunk', ''))
                chunk.setdefault('modality', metadata.get('modality', 'text') if metadata else 'text')
                # Set chunk_id to the generated UUID id
                chunk['chunk_id'] = chunk['id']
            return raw_chunks
    if chunking_strategy == "character":
        return CharacterChunker()
    else:
        raise NotImplementedError(f"Chunking strategy '{chunking_strategy}' not implemented.")

class IngestionService:

    def __init__(self):
        self.processors = {
            'pdf': PDFProcessor(),
            'image': ImageProcessor(),
            'audio': AudioProcessor(),
            'text': TextProcessor()
        }

    def get_processor(self, file_path: Path):
        """Get the appropriate processor for a file"""
        for processor in self.processors.values():
            if processor.can_process(file_path):
                return processor
        return None

    def process_file(self, file_path: Path, chunking_strategy: str = "character",
                    chunk_size: int = 235, chunk_overlap: int = 30) -> Dict[str, Any]:
        """
        Process a single file and return chunks

        Args:
            file_path: Path to the file to process
            chunking_strategy: Strategy for chunking ("character", "sentence", "page")
            chunk_size: Size of each chunk (default 235 for CLIP limit)
            chunk_overlap: Overlap between chunks (default 30 chars)

        Returns:
            Dictionary containing processing results and chunks
        """
        try:
            logger.info(f"Processing file: {file_path}")

            # Get appropriate processor
            processor = self.get_processor(file_path)
            if not processor:
                raise ValueError(f"No processor available for file type: {file_path.suffix}")


            # Extract content
            extraction_result = processor.extract_text(file_path)

            # Handle different extraction result formats
            # Processors now return pre-chunked data with embeddings
            if isinstance(extraction_result, list):
                # Handle empty list case
                if not extraction_result:
                    logger.warning(f"Empty extraction result for {file_path}")
                    return {
                        'status': 'error',
                        'message': 'No content could be extracted from the file',
                        'file_path': str(file_path),
                        'chunks': []
                    }
                
                # Check if this is a pre-chunked result (Audio, Image, or long Text)
                first_item = extraction_result[0]
                
                if 'embedding' in first_item:
                    # Pre-chunked with embeddings (Audio or Image or chunked Text)
                    chunks = []
                    for idx, entry in enumerate(extraction_result):
                        # Determine content field
                        content = entry.get('text') or entry.get('content') or entry.get('ocr_text', '')
                        if entry.get('type') == 'visual' and not content:
                            content = '[IMAGE_VISUAL_EMBEDDING]'
                        
                        # Create chunk with all metadata
                        chunk = {
                            'content': content,
                            'embedding': entry.get('embedding'),
                            'modality': entry.get('modality', 'text'),  # Could be audio, image, text
                            'source_type': entry.get('source_type', 'unknown'),
                            'chunk_index': entry.get('chunk_index', idx),
                            'total_chunks': entry.get('total_chunks', len(extraction_result)),
                            'chunk_id': entry.get('chunk_id'),
                            'prev_chunk_id': entry.get('prev_chunk_id'),
                            'next_chunk_id': entry.get('next_chunk_id'),
                            'metadata': {
                                'source_file': str(file_path),
                                **entry.get('metadata', {})
                            }
                        }
                        
                        # Add modality-specific metadata
                        if 'start' in entry and 'end' in entry:
                            # Audio timestamps
                            chunk['metadata']['timestamps'] = {
                                'start': entry['start'],
                                'end': entry['end']
                            }
                        
                        if entry.get('type') in ['visual', 'ocr']:
                            # Image OCR metadata
                            chunk['metadata']['extraction_type'] = entry['type']
                            chunk['metadata']['ocr_confidence'] = entry.get('ocr_confidence', 0)
                        
                        chunks.append(chunk)
                    
                    total_chars = sum(len(chunk.get('content', '')) for chunk in chunks if chunk.get('content') != '[IMAGE_VISUAL_EMBEDDING]')
                    
                    result = {
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_size': file_path.stat().st_size,
                        'processor_type': type(processor).__name__,
                        'extraction_result': extraction_result,
                        'chunks': chunks,
                        'total_chunks': len(chunks),
                        'chunking_strategy': 'pre-chunked',
                        'chunk_size': 235,  # CLIP limit
                        'chunk_overlap': 30,
                        'total_chars': total_chars,
                        'status': 'success'
                    }
                    logger.info(f"Successfully processed {file_path.name}: {len(chunks)} pre-chunked segments")
                    return result
                
                elif 'page_number' in first_item:
                    # PDF: aggregate all page text, then chunk
                    content = '\n\n'.join(page.get('text', '') for page in extraction_result if page.get('text', '').strip())
                    modality = 'text'
                    metadata = first_item.get('metadata', {})
                    source_type = 'pdf'
                    total_chars = len(content)
                else:
                    # Fallback: treat as text
                    main_result = extraction_result[0]
                    content = main_result.get('content', '')
                    modality = main_result.get('modality', 'text')
                    metadata = main_result.get('metadata', {})
                    source_type = main_result.get('source_type', 'text')
                    total_chars = len(content)
            else:
                # Single result (short text file that wasn't chunked)
                main_result = extraction_result
                content = extraction_result.get('content', '')
                modality = extraction_result.get('modality', 'text')
                metadata = extraction_result.get('metadata', {})
                source_type = extraction_result.get('source_type', 'unknown')
                total_chars = extraction_result.get('total_chars', 0)
                
                # Check if it has chunk metadata (single-chunk text file)
                if 'chunk_index' in extraction_result and 'embedding' not in extraction_result:
                    # Single chunk, needs embedding
                    chunks = [{
                        'content': content,
                        'modality': modality,
                        'source_type': source_type,
                        'chunk_index': extraction_result.get('chunk_index', 0),
                        'total_chunks': extraction_result.get('total_chunks', 1),
                        'prev_chunk_id': extraction_result.get('prev_chunk_id'),
                        'next_chunk_id': extraction_result.get('next_chunk_id'),
                        'metadata': {
                            'source_file': str(file_path),
                            **metadata
                        }
                    }]
                    
                    result = {
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'file_size': file_path.stat().st_size,
                        'processor_type': type(processor).__name__,
                        'extraction_result': extraction_result,
                        'chunks': chunks,
                        'total_chunks': 1,
                        'chunking_strategy': 'single',
                        'chunk_size': 235,
                        'chunk_overlap': 0,
                        'total_chars': total_chars,
                        'status': 'success'
                    }
                    logger.info(f"Successfully processed {file_path.name}: 1 chunk (no splitting needed)")
                    return result

            # Get chunker for content that wasn't pre-chunked (PDFs, legacy)
            chunker = get_chunker(chunking_strategy, chunk_size=chunk_size, overlap=chunk_overlap)

            # Create chunks
            chunks = chunker.chunk_text(
                content,
                metadata={
                    'source_file': str(file_path),
                    'modality': modality,
                    'source_type': source_type,
                    'extraction_metadata': metadata,
                    'total_chars': total_chars
                }
            )

            result = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'processor_type': type(processor).__name__,
                'extraction_result': extraction_result,
                'chunks': [self._chunk_to_dict(chunk) for chunk in chunks],
                'total_chunks': len(chunks),
                'chunking_strategy': chunking_strategy,
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'total_chars': total_chars,
                'status': 'success'
            }

            logger.info(f"Successfully processed {file_path.name}: {len(chunks)} chunks created")
            return result

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'error': str(e),
                'status': 'failed'
            }

    def process_batch(self, file_paths: List[Path], chunking_strategy: str = "character",
                     chunk_size: int = 235, chunk_overlap: int = 30,
                     max_workers: int = 4) -> List[Dict[str, Any]]:
        """
        Process multiple files in parallel

        Args:
            file_paths: List of file paths to process
            chunking_strategy: Strategy for chunking
            chunk_size: Size of each chunk (default 235 for CLIP limit)
            chunk_overlap: Overlap between chunks (default 30 chars)
            max_workers: Maximum number of parallel workers

        Returns:
            List of processing results
        """
        logger.info(f"Processing batch of {len(file_paths)} files")

        results = []

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.process_file, file_path, chunking_strategy,
                              chunk_size, chunk_overlap): file_path
                for file_path in file_paths
            }

            # Collect results as they complete
            for future in as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch processing failed for {file_path}: {e}")
                    results.append({
                        'file_path': str(file_path),
                        'file_name': file_path.name,
                        'error': str(e),
                        'status': 'failed'
                    })

        # Sort results by original order
        results.sort(key=lambda x: file_paths.index(Path(x['file_path'])))

        successful = sum(1 for r in results if r.get('status') == 'success')
        logger.info(f"Batch processing completed: {successful}/{len(results)} files successful")

        return results

    def get_file_summary(self, file_path: Path) -> Dict[str, Any]:
        """
        Get summary information about a file without full processing

        Args:
            file_path: Path to the file

        Returns:
            Summary dictionary
        """
        try:
            processor = self.get_processor(file_path)
            if processor:
                return processor.get_summary(file_path)
            else:
                return {
                    'file_name': file_path.name,
                    'file_size': file_path.stat().st_size,
                    'can_process': False,
                    'error': 'Unsupported file type'
                }
        except Exception as e:
            logger.error(f"Failed to get summary for {file_path}: {e}")
            return {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'can_process': False,
                'error': str(e)
            }

    def validate_files(self, file_paths: List[Path]) -> Dict[str, Any]:
        """
        Validate a list of files for processing

        Args:
            file_paths: List of file paths to validate

        Returns:
            Validation results
        """
        valid_files = []
        invalid_files = []

        for file_path in file_paths:
            if file_path.exists():
                processor = self.get_processor(file_path)
                if processor:
                    valid_files.append(str(file_path))
                else:
                    invalid_files.append({
                        'file_path': str(file_path),
                        'error': 'Unsupported file type'
                    })
            else:
                invalid_files.append({
                    'file_path': str(file_path),
                    'error': 'File does not exist'
                })

        return {
            'valid_files': valid_files,
            'invalid_files': invalid_files,
            'total_valid': len(valid_files),
            'total_invalid': len(invalid_files)
        }

    def _chunk_to_dict(self, chunk: dict) -> Dict[str, Any]:
        """Convert chunk object to dictionary (for compatibility)"""
        return dict(chunk) if isinstance(chunk, dict) else {}