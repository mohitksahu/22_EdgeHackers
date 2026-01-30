from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
from app.ingestion.chunking.text_chunker import micro_chunk_text
import re
"""
Audio processor using faster-whisper for transcription (C++-powered, CTranslate2)
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

from faster_whisper import WhisperModel

from app.config import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Processor for audio files using faster-whisper (CTranslate2 engine)"""

    def __init__(self):
        self.supported_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']
        self.model = None
        self.model_name = getattr(settings, 'WHISPER_MODEL', 'base')
        self.device = "cpu"  # Move to CPU to save VRAM for Llama
        self.compute_type = "int8"  # Optimized for CPU speed

    def _load_model(self):
        """Load faster-whisper model if not already loaded"""
        if self.model is None:
            logger.info(f"Loading faster-whisper model: {self.model_name}")
            logger.info(f"Device: {self.device}, Compute type: {self.compute_type}")
            
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(settings.models_dir / "whisper")
            )
            
            logger.info("faster-whisper model loaded successfully (CTranslate2 engine)")
            logger.info(f"[faster-whisper] Running on CPU with int8 precision for VRAM optimization")

    def can_process(self, file_path: Path) -> bool:
        """Check if the processor can handle the file"""
        return file_path.suffix.lower() in self.supported_extensions

    def extract_text(self, file_path: Path):
        """
        Transcribe audio file using faster-whisper, aggregate full transcript, chunk properly, embed each chunk.
        Returns: List[Dict] with chunked text, timestamps, embeddings, and complete metadata.
        """
        try:
            logger.info(f"Processing audio: {file_path}")
            self._load_model()
            # Use absolute path and ensure it exists
            audio_path = file_path.resolve()
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Step 1: Transcribe full audio using faster-whisper
            segments_iter, info = self.model.transcribe(
                str(audio_path),
                beam_size=5,
                language=None  # Auto-detect language
            )
            
            # Convert iterator to list and extract segments
            segments = list(segments_iter)
            
            metadata = {
                'duration': info.duration,
                'language': info.language,
                'file_size': file_path.stat().st_size,
            }
            
            # Step 2: Aggregate FULL transcript (NO truncation)
            full_transcript = ' '.join(seg.text.strip() for seg in segments if seg.text.strip())
            transcript_length = len(full_transcript)
            
            logger.info(f"Full transcript length: {transcript_length} chars")
            
            # Step 3: Check if chunking is needed
            if transcript_length <= 235:
                # Single chunk - no splitting needed
                embedder = MultimodalEmbedder()
                embedding = embedder.embed(full_transcript)
                processed_segments = [{
                    'text': full_transcript,
                    'start': float(segments[0].start) if segments else 0.0,
                    'end': float(segments[-1].end) if segments else metadata['duration'],
                    'embedding': embedding,
                    'metadata': metadata,
                    'file_path': str(file_path),
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'prev_chunk_id': None,
                    'next_chunk_id': None
                }]
                logger.info(f"Audio processed: 1 chunk (no splitting needed)")
            else:
                # Multiple chunks needed - split transcript
                logger.info(f"Transcript exceeds embedding limit — splitting into chunks")
                chunks = micro_chunk_text(full_transcript, chunk_size=235, chunk_overlap=30)
                
                embedder = MultimodalEmbedder()
                processed_segments = []
                
                # Calculate timestamp distribution (best-effort)
                total_duration = metadata['duration']
                chars_per_second = transcript_length / total_duration if total_duration > 0 else 0
                
                cumulative_chars = 0
                for chunk_data in chunks:
                    chunk_text = chunk_data['chunk']
                    chunk_length = len(chunk_text)
                    
                    # Estimate timestamps based on character position
                    start_time = cumulative_chars / chars_per_second if chars_per_second > 0 else 0
                    end_time = (cumulative_chars + chunk_length) / chars_per_second if chars_per_second > 0 else total_duration
                    
                    # Embed the chunk
                    embedding = embedder.embed(chunk_text)
                    
                    processed_segments.append({
                        'text': chunk_text,
                        'start': float(start_time),
                        'end': float(end_time),
                        'embedding': embedding,
                        'metadata': metadata,
                        'file_path': str(file_path),
                        'chunk_id': chunk_data['id'],
                        'prev_chunk_id': chunk_data['prev_chunk_id'],
                        'next_chunk_id': chunk_data['next_chunk_id']
                    })
                    
                    cumulative_chars += chunk_length
                
                logger.info(f"Audio processed: {len(processed_segments)} chunks stored")
            
            return processed_segments
            
        except Exception as e:
            logger.error(f"Failed to process audio {file_path}: {e}")
            raise Exception(f"Audio processing failed: {str(e)}")

    def extract_segments(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extract individual segments as separate chunks

        Args:
            file_path: Path to the audio file

        Returns:
            List of segment dictionaries
        """
        result = self.extract_text(file_path)
        segments = result['segments']

        # Add source metadata to each segment
        for segment in segments:
            segment.update({
                'source_file': str(file_path),
                'modality': 'text',
                'source_type': 'audio',
                'metadata': result['metadata']
            })

        return segments

    def get_summary(self, file_path: Path) -> Dict[str, Any]:
        """
        Get a summary of the audio file without full transcription

        Args:
            file_path: Path to the audio file

        Returns:
            Summary dictionary
        """
        try:
            # Get basic file info
            file_size = file_path.stat().st_size

            # Get duration using faster-whisper info
            self._load_model()
            audio_path = file_path.resolve()
            
            # Transcribe with minimal processing to get info
            _, info = self.model.transcribe(
                str(audio_path),
                beam_size=1,
                language=None
            )

            return {
                'file_name': file_path.name,
                'file_size': file_size,
                'duration': info.duration,
                'can_process': True
            }

        except Exception as e:
            logger.error(f"Failed to get audio summary: {e}")
            return {
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'can_process': False,
                'error': str(e)
            }