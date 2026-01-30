"""
Text file processor for plain text documents
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.config import settings
from app.ingestion.chunking.text_chunker import micro_chunk_text

logger = logging.getLogger(__name__)


class TextProcessor:
    """Processor for plain text files"""

    def __init__(self):
        self.supported_extensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html']

    def can_process(self, file_path: Path) -> bool:
        """Check if the processor can handle the file"""
        return file_path.suffix.lower() in self.supported_extensions

    def detect_encoding(self, file_path: Path) -> str:
        """
        Detect the encoding of a text file

        Args:
            file_path: Path to the text file

        Returns:
            Detected encoding string
        """
        try:
            import chardet

            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8')
        except ImportError:
            # Fallback if chardet is not available
            return 'utf-8'
        except Exception:
            return 'utf-8'

    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract text content from file

        Args:
            file_path: Path to the text file

        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            logger.info(f"Processing text file: {file_path}")

            # Detect encoding
            encoding = self.detect_encoding(file_path)

            # Read file content
            with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                content = file.read()

            # Get metadata
            metadata = {
                'encoding': encoding,
                'file_size': file_path.stat().st_size,
                'line_count': len(content.splitlines()),
            }

            # For structured formats, add additional metadata
            if file_path.suffix.lower() == '.json':
                try:
                    import json
                    json_data = json.loads(content)
                    metadata['json_keys'] = list(json_data.keys()) if isinstance(json_data, dict) else len(json_data)
                    metadata['is_valid_json'] = True
                except:
                    metadata['is_valid_json'] = False

            elif file_path.suffix.lower() == '.csv':
                try:
                    import csv
                    from io import StringIO
                    csv_reader = csv.reader(StringIO(content))
                    rows = list(csv_reader)
                    metadata['csv_rows'] = len(rows)
                    metadata['csv_columns'] = len(rows[0]) if rows else 0
                    metadata['is_valid_csv'] = True
                except:
                    metadata['is_valid_csv'] = False

            # Check if chunking is needed
            if len(content) <= 235:
                # Single chunk
                result = {
                    'content': content,
                    'metadata': metadata,
                    'total_chars': len(content),
                    'modality': 'text',
                    'source_type': 'text',
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'prev_chunk_id': None,
                    'next_chunk_id': None
                }
                logger.info(f"Successfully processed text file: {len(content)} characters (1 chunk)")
            else:
                # Multiple chunks needed
                logger.info(f"Text content exceeds embedding limit — splitting into chunks")
                chunks = micro_chunk_text(content, chunk_size=235, chunk_overlap=30)
                
                # Return as list of chunks with metadata
                result = []
                for i, chunk_data in enumerate(chunks):
                    result.append({
                        'content': chunk_data['chunk'],
                        'metadata': metadata,
                        'total_chars': len(content),
                        'modality': 'text',
                        'source_type': 'text',
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'chunk_id': chunk_data['id'],
                        'prev_chunk_id': chunk_data['prev_chunk_id'],
                        'next_chunk_id': chunk_data['next_chunk_id'],
                        'file_path': str(file_path)
                    })
                logger.info(f"Successfully processed text file: {len(result)} chunks created")
            
            return result

        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {e}")
            raise Exception(f"Text processing failed: {str(e)}")

    def extract_lines(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract individual lines as separate chunks

        Args:
            file_path: Path to the text file

        Returns:
            List of line dictionaries
        """
        result = self.extract_text(file_path)
        lines = result['content'].splitlines()

        # Create chunks for each line
        chunks = []
        for i, line in enumerate(lines):
            if line.strip():  # Skip empty lines
                chunks.append({
                    'content': line.strip(),
                    'line_number': i + 1,
                    'source_file': str(file_path),
                    'modality': 'text',
                    'source_type': 'text',
                    'metadata': result['metadata']
                })

        return chunks

    def get_summary(self, file_path: Path) -> Dict[str, Any]:
        """
        Get a summary of the text file without full content extraction

        Args:
            file_path: Path to the text file

        Returns:
            Summary dictionary
        """
        try:
            encoding = self.detect_encoding(file_path)

            with open(file_path, 'r', encoding=encoding, errors='replace') as file:
                content = file.read()

            return {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'encoding': encoding,
                'line_count': len(content.splitlines()),
                'char_count': len(content),
                'can_process': True
            }

        except Exception as e:
            logger.error(f"Failed to get text file summary: {e}")
            return {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'can_process': False,
                'error': str(e)
            }