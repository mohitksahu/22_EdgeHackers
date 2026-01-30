"""
Ingestion Orchestrator — STRICT scope isolation + topic hygiene
"""
import logging
import uuid
import re
from pathlib import Path
from typing import List, Dict, Any

from app.ingestion.ingestion_service import IngestionService
from app.storage.vector_store import VectorStore
from app.embeddings.manager import EmbeddingsManager
from app.reasoning.llm.llama_reasoner import LlamaReasoner

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """
    Responsible for:
    - File ingestion
    - Chunk preparation
    - Metadata sanitation
    - Scope-safe vector storage
    """

    def __init__(self):
        self.ingestion_service = IngestionService()
        self.vector_store = VectorStore()
        self.embedder = EmbeddingsManager()
        self.llm = LlamaReasoner()

    # ---------------------------------------------------------
    # 🔑 FALLBACK TOPIC EXTRACTION
    # ---------------------------------------------------------
    def _infer_topic(self, text: str) -> str:
        """
        Infer topic from content if extractor fails.
        """
        text = text.lower()

        if "photosynthesis" in text:
            return "photosynthesis"
        if "cell" in text:
            return "cell biology"
        if "economics" in text:
            return "economics"

        # fallback: first noun-like word
        words = re.findall(r"[a-zA-Z]{4,}", text)
        return words[0] if words else "general"

    def _infer_concepts(self, text: str) -> str:
        """
        Infer basic concepts from content.
        """
        concepts = set()

        keywords = [
            "photosynthesis",
            "chlorophyll",
            "sunlight",
            "carbon dioxide",
            "oxygen",
            "glucose",
            "plants",
        ]

        lower = text.lower()
        for kw in keywords:
            if kw in lower:
                concepts.add(kw)

        return ", ".join(sorted(concepts))

    # ---------------------------------------------------------
    # INGESTION ENTRY
    # ---------------------------------------------------------
    def ingest_and_store(
        self,
        file_path: Path,
        scope_id: str,
        chunking_strategy: str = "character",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Dict[str, Any]:

        try:
            logger.info(f"Starting ingestion for {file_path} | scope={scope_id}")

            # 🔑 CLEAR PREVIOUS DOCUMENTS - Single document mode
            # cleared_count = self.vector_store.clear_collection()
            # logger.info(f"Cleared {cleared_count} previous documents for single-document mode")

            processing = self.ingestion_service.process_file(
                file_path,
                chunking_strategy=chunking_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            if processing.get("status") != "success":
                return processing

            chunks = processing.get("chunks", [])
            prepared: List[Dict[str, Any]] = []

            for i, chunk in enumerate(chunks):
                content = chunk.get("content", "").strip()
                if not content:
                    continue

                raw_meta = chunk.get("metadata", {}) or {}

                # -------------------------------
                # 🔑 TOPIC FIX
                # -------------------------------
                topic = raw_meta.get("document_topic")
                if not topic or topic.lower() == "unknown":
                    topic = self._infer_topic(content)

                # -------------------------------
                # 🔑 CONCEPT FIX
                # -------------------------------
                concepts = raw_meta.get("document_concepts")
                if not concepts:
                    concepts = self._infer_concepts(content)

                prepared.append({
                    "chunk_id": chunk.get("chunk_id", str(uuid.uuid4())),
                    "content": content,
                    "embedding": chunk.get("embedding")
                    or self.embedder.embed_text(content),

                    # 🔑 METADATA — FINAL, CLEAN, CONSISTENT
                    "metadata": {
                        "scope_id": scope_id,  # 🔥 NOT planet_id
                        "source_file": str(file_path),
                        "file_name": file_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "document_topic": topic.lower(),
                        "document_concepts": concepts.lower(),
                        "modality": chunk.get("modality", "text"),
                    },
                })

                logger.debug(f"[INGESTION] Generated embedding for chunk {i}: {len(prepared[-1]['embedding'])}D")

            store = self.vector_store.add_documents(prepared)

            logger.info(
                f"Ingestion complete | stored={store.get('count', 0)} chunks | scope={scope_id}"
            )

            return {
                **processing,
                "status": "success",
                "stored_chunks": store.get("count", 0),
                "scope_id": scope_id,
            }

        except Exception as e:
            logger.exception("Ingestion failed")
            return {
                "status": "failed",
                "error": str(e),
                "scope_id": scope_id,
            }
