"""
Metadata extraction utilities
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from files and content"""

    def __init__(self):
        pass

    def extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract basic file metadata

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file metadata
        """
        try:
            stat = file_path.stat()

            metadata = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'file_extension': file_path.suffix.lower(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_readable': True
            }

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract file metadata for {file_path}: {e}")
            return {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'error': str(e),
                'is_readable': False
            }

    def extract_content_metadata(self, content: str, source_type: str) -> Dict[str, Any]:
        """
        Extract metadata from content

        Args:
            content: Text content
            source_type: Type of source (pdf, text, audio, etc.)

        Returns:
            Dictionary with content metadata
        """
        try:
            metadata = {
                'content_length': len(content),
                'word_count': len(content.split()),
                'line_count': len(content.splitlines()),
                'source_type': source_type,
                'has_content': bool(content.strip())
            }

            # Calculate average word length
            words = content.split()
            if words:
                avg_word_length = sum(len(word) for word in words) / len(words)
                metadata['avg_word_length'] = round(avg_word_length, 2)

            # Language detection (simple heuristic)
            metadata['estimated_language'] = self._estimate_language(content)

            # Content type detection
            metadata['content_type'] = self._detect_content_type(content)

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract content metadata: {e}")
            return {
                'content_length': len(content),
                'error': str(e)
            }

    def extract_processing_metadata(self, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from processing results

        Args:
            processing_result: Result from ingestion processing

        Returns:
            Dictionary with processing metadata
        """
        try:
            metadata = {
                'processing_status': processing_result.get('status', 'unknown'),
                'processing_time': processing_result.get('processing_time'),
                'chunk_count': processing_result.get('total_chunks', 0),
                'chunking_strategy': processing_result.get('chunking_strategy', 'unknown'),
                'chunk_size': processing_result.get('chunk_size', 0),
                'chunk_overlap': processing_result.get('chunk_overlap', 0),
                'total_chars': processing_result.get('total_chars', 0)
            }

            # Add extraction metadata if available
            if 'extraction_result' in processing_result:
                extraction = processing_result['extraction_result']
                # If extraction is a list (e.g., image), use the first entry for modality/source_type
                if isinstance(extraction, list) and extraction:
                    first = extraction[0]
                    # Check if this is a PDF (has page_number), Audio (has start/end), or Image (has type)
                    if 'page_number' in first:
                        # PDF extraction
                        metadata.update({
                            'extraction_modality': 'text',
                            'extraction_source_type': 'pdf'
                        })
                    elif 'start' in first and 'end' in first:
                        # Audio extraction
                        metadata.update({
                            'extraction_modality': 'audio',
                            'extraction_source_type': 'audio'
                        })
                    else:
                        # Image extraction
                        metadata.update({
                            'extraction_modality': first.get('type'),
                            'extraction_source_type': first.get('source_type', 'image')
                        })
                elif isinstance(extraction, dict):
                    metadata.update({
                        'extraction_modality': extraction.get('modality'),
                        'extraction_source_type': extraction.get('source_type')
                    })

                # Add modality-specific metadata
                if isinstance(extraction, dict) and extraction.get('modality') == 'text':
                    if extraction.get('source_type') == 'pdf':
                        metadata.update({
                            'pdf_pages': extraction.get('metadata', {}).get('pages', 0),
                            'pdf_title': extraction.get('metadata', {}).get('title')
                        })
                    elif extraction.get('source_type') == 'audio':
                        metadata.update({
                            'audio_duration': extraction.get('metadata', {}).get('duration', 0),
                            'audio_language': extraction.get('metadata', {}).get('language')
                        })
                # Add metadata for audio list results (from Whisper segments)
                elif isinstance(extraction, list) and extraction and 'start' in extraction[0]:
                    first_segment = extraction[0]
                    segment_metadata = first_segment.get('metadata', {})
                    metadata.update({
                        'audio_duration': segment_metadata.get('duration', 0),
                        'audio_language': segment_metadata.get('language', 'unknown')
                    })

            return metadata

        except Exception as e:
            logger.error(f"Failed to extract processing metadata: {e}")
            return {
                'processing_status': 'error',
                'error': str(e)
            }

    def _estimate_language(self, text: str) -> str:
        """Simple language estimation based on character patterns"""
        text = text.lower()

        # English patterns
        english_chars = sum(1 for c in text if c in 'abcdefghijklmnopqrstuvwxyz ')
        english_ratio = english_chars / len(text) if text else 0

        # Check for common non-English characters
        cyrillic_chars = sum(1 for c in text if ord(c) in range(1024, 1279))
        chinese_chars = sum(1 for c in text if ord(c) in range(19968, 40959))

        if chinese_chars > len(text) * 0.3:
            return 'chinese'
        elif cyrillic_chars > len(text) * 0.3:
            return 'cyrillic'
        elif english_ratio > 0.8:
            return 'english'
        else:
            return 'unknown'

    def _detect_content_type(self, content: str) -> str:
        """Detect the type of content"""
        content_lower = content.lower()

        # Code detection
        code_indicators = ['import ', 'function ', 'class ', 'def ', 'public ', 'private ', 'const ', 'let ']
        if any(indicator in content_lower for indicator in code_indicators):
            return 'code'

        # JSON detection
        if content.strip().startswith('{') and content.strip().endswith('}'):
            try:
                import json
                json.loads(content)
                return 'json'
            except:
                pass

        # CSV detection
        lines = content.split('\n')[:5]  # Check first 5 lines
        if len(lines) > 1:
            commas = [line.count(',') for line in lines if line.strip()]
            if commas and all(count == commas[0] for count in commas) and commas[0] > 0:
                return 'csv'

        # Markdown detection
        if any(line.strip().startswith(('# ', '## ', '### ', '- ', '* ', '1. ')) for line in lines):
            return 'markdown'

        # Default to plain text
        return 'text'

    def combine_metadata(self, *metadata_dicts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine multiple metadata dictionaries

        Args:
            *metadata_dicts: Metadata dictionaries to combine

        Returns:
            Combined metadata dictionary
        """
        combined = {}

        for metadata in metadata_dicts:
            if metadata:
                combined.update(metadata)

        # Add combination timestamp
        combined['combined_at'] = datetime.now().isoformat()

        return combined