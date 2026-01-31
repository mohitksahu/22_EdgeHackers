"""
Ingestion Orchestrator - Routes files to appropriate processors and stores embeddings
"""
import uuid
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from app.config import settings
from app.core.logging_config import get_safe_logger

logger = get_safe_logger(__name__)


class IngestionOrchestrator:
    """
    Orchestrates the document ingestion pipeline:
    1. Routes files to appropriate processor
    2. Generates CLIP embeddings for all content
    3. Stores in Qdrant vector database with metadata
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IngestionOrchestrator, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if IngestionOrchestrator._initialized:
            return
        
        self._vector_store = None
        self._embeddings_manager = None
        self._processors = None
        self._llm = None
        
        IngestionOrchestrator._initialized = True
        logger.info("[OK] IngestionOrchestrator initialized")
    
    @property
    def vector_store(self):
        if self._vector_store is None:
            from app.storage.vector_store import VectorStore
            self._vector_store = VectorStore()
        return self._vector_store
    
    @property
    def embeddings_manager(self):
        if self._embeddings_manager is None:
            from app.embeddings.manager import EmbeddingsManager
            self._embeddings_manager = EmbeddingsManager()
        return self._embeddings_manager
    
    @property
    def processors(self):
        if self._processors is None:
            from app.ingestion.processors import (
                TextProcessor, ImageProcessor, AudioProcessor, PDFProcessor
            )
            self._processors = {
                'text': TextProcessor(),
                'image': ImageProcessor(),
                'audio': AudioProcessor(),
                'pdf': PDFProcessor(),  # Dedicated PDF processor
            }
        return self._processors
    
    @property
    def llm(self):
        if self._llm is None:
            try:
                from app.reasoning.llm.ollama_reasoner import OllamaReasoner
                self._llm = OllamaReasoner()
            except Exception as e:
                logger.warning(f"[WARN] Ollama init failed: {e}")
        return self._llm
    
    def ingest_and_store(
        self,
        file_path: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main ingestion pipeline:
        1. Determine file type and get processor
        2. Process file into chunks
        3. Generate CLIP embeddings
        4. Store in Qdrant with metadata
        """
        file_path = Path(file_path)
        metadata = metadata or {}
        
        logger.info(f"[START] Processing: {file_path.name}")
        
        try:
            # Get appropriate processor
            processor = self._get_processor(file_path)
            processor_name = processor.__class__.__name__
            
            logger.info(f"[ANALYZE] Using {processor_name} for {file_path.suffix}")
            
            # Process file into chunks
            chunks = processor.process(str(file_path), metadata)
            
            if not chunks:
                logger.warning(f"[WARN] No content extracted from {file_path.name}")
                return {
                    "status": "warning",
                    "message": "No content extracted",
                    "chunks": 0,
                    "indexed": 0
                }
            
            logger.info(f"[OK] Extracted {len(chunks)} chunks")
            
            # Extract document knowledge (topic, concepts) using LLM
            document_topic, document_concepts = self._extract_document_knowledge(
                chunks, file_path
            )
            
            logger.info(f"[STATS] Document metadata:")
            logger.info(f"  [TAG] Topic: '{document_topic}'")
            if document_concepts:
                logger.info(f"  [KEY] Concepts: {document_concepts[:5]}...")
            
            # Prepare chunks with CLIP embeddings
            prepared = self._prepare_chunks_with_embeddings(
                chunks=chunks,
                session_id=session_id,
                document_topic=document_topic,
                document_concepts=document_concepts,
                source_file=str(file_path),
                metadata=metadata
            )
            
            # Log summary by modality
            modality_counts = {}
            for c in prepared:
                mod = c.get('payload', {}).get('modality', 'unknown')
                modality_counts[mod] = modality_counts.get(mod, 0) + 1
            
            logger.info(f"[PKG] Prepared {len(prepared)} chunks:")
            for mod, count in modality_counts.items():
                logger.info(f"  [{mod.upper()}]: {count}")
            
            # Store in Qdrant vector database
            result = self.vector_store.add_documents(prepared)
            
            if result.get('status') == 'success':
                logger.info(f"[OK] Indexed {result.get('indexed', 0)} documents")
                return {
                    "status": "success",
                    "message": f"Ingested {file_path.name}",
                    "chunks": len(prepared),
                    "indexed": result.get('indexed', 0),
                    "topic": document_topic,
                    "concepts": document_concepts,
                    "modalities": modality_counts
                }
            else:
                raise Exception(result.get('message', 'Storage error'))
                
        except Exception as e:
            logger.error(f"[FAIL] Ingestion failed for {file_path.name}: {e}")
            raise
    
    def _get_processor(self, file_path: Path):
        """Get appropriate processor for file type"""
        suffix = file_path.suffix.lower()
        
        # PDF gets dedicated processor (extracts both text AND images)
        if suffix == '.pdf':
            return self.processors['pdf']
        
        # Extension mapping for other file types
        extension_map = {
            # Text files
            '.txt': 'text',
            '.md': 'text',
            '.html': 'text',
            '.htm': 'text',
            '.json': 'text',
            '.xml': 'text',
            '.csv': 'text',
            # Image files
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.webp': 'image',
            '.tiff': 'image',
            '.tif': 'image',
            # Audio files
            '.mp3': 'audio',
            '.wav': 'audio',
            '.m4a': 'audio',
            '.ogg': 'audio',
            '.flac': 'audio',
            '.aac': 'audio',
            '.wma': 'audio',
        }
        
        processor_type = extension_map.get(suffix, 'text')
        return self.processors[processor_type]
    
    def _extract_document_knowledge(
        self,
        chunks: List[Dict[str, Any]],
        file_path: Path
    ) -> Tuple[str, List[str]]:
        """Extract topic and concepts using LLM"""
        # Collect text samples
        samples = []
        for chunk in chunks[:5]:
            content = chunk.get('content', '')
            if content and len(content) > 30:
                samples.append(content[:400])
        
        combined = " ".join(samples)
        
        if not combined or len(combined) < 50:
            return self._topic_from_filename(file_path), []
        
        # Try LLM extraction
        if self.llm:
            try:
                logger.info("  [ANALYZE] Extracting topic with LLM...")
                
                prompt = f"""Analyze this document and extract:
1. TOPIC: Main subject (2-4 words)
2. CONCEPTS: Key terms (5-10 single words)

Text: {combined[:1500]}

Format:
TOPIC: <topic>
CONCEPTS: <word1>, <word2>, ...

Response:"""
                
                response = self.llm.generate(prompt, max_tokens=100, temperature=0.1)
                topic, concepts = self._parse_llm_response(response, file_path)
                
                if topic:
                    logger.info(f"  [OK] LLM extracted topic: '{topic}' with {len(concepts)} concepts")
                    return topic, concepts
                    
            except Exception as e:
                logger.warning(f"  [WARN] LLM extraction failed: {e}")
        
        return self._topic_from_filename(file_path), []
    
    def _parse_llm_response(
        self, response: str, file_path: Path
    ) -> Tuple[str, List[str]]:
        """Parse LLM topic/concepts response"""
        topic = None
        concepts = []
        
        for line in response.split('\n'):
            line = line.strip()
            if line.upper().startswith('TOPIC:'):
                topic = line.split(':', 1)[1].strip().strip('"\'')
            elif line.upper().startswith('CONCEPTS:'):
                parts = line.split(':', 1)[1].strip()
                concepts = [c.strip().lower() for c in parts.split(',') if c.strip()]
        
        if not topic or topic.lower() in ['unknown', 'none', '']:
            topic = self._topic_from_filename(file_path)
        
        return topic, concepts[:15]
    
    def _topic_from_filename(self, file_path: Path) -> str:
        """Extract topic from filename"""
        name = file_path.stem
        name = name.replace('_', ' ').replace('-', ' ')
        # Remove UUID prefixes
        parts = name.split()
        if parts and len(parts[0]) == 8 and parts[0].isalnum():
            parts = parts[1:]
        return ' '.join(word.capitalize() for word in parts) or "General Document"
    
    def _prepare_chunks_with_embeddings(
        self,
        chunks: List[Dict[str, Any]],
        session_id: str,
        document_topic: str,
        document_concepts: List[str],
        source_file: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prepare chunks with CLIP embeddings:
        - Text content -> text embedding
        - Image data -> image embedding
        - Audio transcription -> text embedding
        """
        prepared = []
        total = len(chunks)
        
        for i, chunk in enumerate(chunks):
            try:
                content = chunk.get('content', '')
                modality = chunk.get('modality', 'text')
                chunk_id = chunk.get('chunk_id', str(uuid.uuid4()))
                
                # Generate embeddings using CLIP
                text_embedding = None
                image_embedding = None
                
                # 1. Text embedding (for text content - works for all modalities)
                if content and len(content.strip()) > 10:
                    try:
                        text_embedding = self.embeddings_manager.embed_text(content)
                    except Exception as e:
                        logger.warning(f"[WARN] Text embedding failed for chunk {i}: {e}")
                
                # 2. Image embedding (only for image modality with image_data)
                if chunk.get('image_data'):
                    try:
                        image_embedding = self.embeddings_manager.embed_image_bytes(
                            chunk['image_data']
                        )
                    except Exception as e:
                        logger.warning(f"[WARN] Image embedding failed for chunk {i}: {e}")
                
                # Skip if no embeddings generated
                if text_embedding is None and image_embedding is None:
                    logger.warning(f"[SKIP] No embeddings for chunk {i}")
                    continue
                
                # Build rich payload with metadata for retrieval/justification
                payload = {
                    'chunk_id': chunk_id,
                    'content': content[:5000],  # Limit content size
                    'modality': modality,
                    'source_type': chunk.get('source_type', modality),
                    'source_file': source_file,
                    'file_name': Path(source_file).name,
                    'session_id': session_id,
                    'document_topic': document_topic,
                    'document_concepts': document_concepts,
                    'chunk_index': i,
                    'total_chunks': total,
                }
                
                # Add processor-specific metadata for source justification
                metadata_keys = [
                    'page_number', 'total_pages', 'pdf_id', 'source_pdf',
                    'image_path', 'image_filename', 'width', 'height', 
                    'description', 'ocr_text', 'ocr_confidence',
                    'transcription', 'duration',
                ]
                for key in metadata_keys:
                    if key in chunk:
                        payload[key] = chunk[key]
                
                prepared.append({
                    'id': chunk_id,
                    'text_embedding': text_embedding,
                    'image_embedding': image_embedding,
                    'audio_embedding': None,  # Audio uses text embedding of transcription
                    'payload': payload
                })
                
            except Exception as e:
                logger.error(f"[FAIL] Chunk {i} preparation failed: {e}")
        
        return prepared