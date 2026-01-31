"""
Audio Processor - Transcribe audio using Whisper and create text embeddings
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid

from app.core.logging_config import get_safe_logger
from app.ingestion.processors.base_processor import BaseProcessor
from app.config import settings

logger = get_safe_logger(__name__)


class AudioProcessor(BaseProcessor):
    """Process audio files with Whisper transcription"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma']
        self._whisper_model = None
        self.chunk_size = 512
        self.chunk_overlap = 50
    
    @property
    def whisper_model(self):
        """Lazy load Whisper model"""
        if self._whisper_model is None:
            try:
                from faster_whisper import WhisperModel
                
                # Use CPU with int8 for VRAM efficiency
                self._whisper_model = WhisperModel(
                    "base",
                    device="cpu",
                    compute_type="int8"
                )
                logger.info("[OK] Faster-Whisper model loaded (CPU, int8)")
            except Exception as e:
                logger.error(f"[FAIL] Whisper init failed: {e}")
                self._whisper_model = False
        
        return self._whisper_model if self._whisper_model else None
    
    def process(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Process audio file and return transcription chunks"""
        file_path = Path(file_path)
        metadata = metadata or {}
        
        logger.info(f"Processing audio: {file_path}")
        
        if not self.whisper_model:
            logger.error("[FAIL] Whisper model not available")
            return []
        
        try:
            # Transcribe audio
            segments, info = self.whisper_model.transcribe(
                str(file_path),
                beam_size=5,
                language="en",
                vad_filter=True
            )
            
            # Collect full transcription
            full_text = ""
            for segment in segments:
                full_text += segment.text + " "
            
            full_text = full_text.strip()
            
            if not full_text:
                logger.warning(f"No speech detected in {file_path.name}")
                return []
            
            logger.info(f"Transcribed {info.duration:.1f}s audio: {len(full_text)} chars")
            
            # Create chunks from transcription
            chunks = self._create_chunks(
                text=full_text,
                file_path=file_path,
                duration=info.duration,
                metadata=metadata
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"[FAIL] Audio processing failed: {e}")
            raise
    
    def _create_chunks(
        self,
        text: str,
        file_path: Path,
        duration: float,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create chunks from transcription"""
        chunks = []
        
        # Single chunk if short
        if len(text) <= self.chunk_size:
            chunks.append({
                'chunk_id': str(uuid.uuid4()),
                'content': text,
                'modality': 'audio',
                'source_type': 'audio',
                'chunk_index': 0,
                'total_chunks': 1,
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'processor_type': 'AudioProcessor',
                'duration': duration,
                'transcription': text,
            })
            return chunks
        
        # Split into chunks
        words = text.split()
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for word in words:
            word_length = len(word)
            
            if current_length + word_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': str(uuid.uuid4()),
                    'content': chunk_text,
                    'modality': 'audio',
                    'source_type': 'audio',
                    'chunk_index': chunk_index,
                    'file_name': file_path.name,
                    'file_path': str(file_path),
                    'file_size': file_path.stat().st_size,
                    'processor_type': 'AudioProcessor',
                    'duration': duration,
                    'transcription': chunk_text,
                })
                
                # Keep overlap
                overlap_words = current_chunk[-5:] if len(current_chunk) > 5 else []
                current_chunk = overlap_words
                current_length = sum(len(w) for w in overlap_words)
                chunk_index += 1
            
            current_chunk.append(word)
            current_length += word_length + 1
        
        # Final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': str(uuid.uuid4()),
                'content': chunk_text,
                'modality': 'audio',
                'source_type': 'audio',
                'chunk_index': chunk_index,
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'processor_type': 'AudioProcessor',
                'duration': duration,
                'transcription': chunk_text,
            })
        
        # Update totals
        total = len(chunks)
        for chunk in chunks:
            chunk['total_chunks'] = total
        
        logger.info(f"Audio transcription split into {total} chunks")
        return chunks