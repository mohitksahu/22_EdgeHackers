"""
Retrieval graph node
"""
import logging
from typing import Dict, Any

from app.retrieval.orchestrator import RetrievalOrchestrator
from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
from app.storage.chromadb.client import ChromaDBClient
from app.config import settings

logger = logging.getLogger(__name__)


class RetrievalNode:
    def __init__(self):
        self.orchestrator = RetrievalOrchestrator()
        self.embedder = MultimodalEmbedder()
        self.vector_store = ChromaDBClient()

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state["query"]
        scope_id = state.get("scope_id")

        query_embedding = self.embedder.encode_text([query])[0]

        logger.info(f"[RETRIEVAL NODE] Planet-level retrieval | scope={scope_id}")

        where = {"scope_id": scope_id} if scope_id is not None else None
        raw_results = self.vector_store.query_documents(
            query_embedding=query_embedding,
            n_results=20,
            where=where
        )

        # Format results
        formatted = []
        if raw_results and raw_results.get("documents"):
            documents = raw_results["documents"][0]
            metadatas = raw_results["metadatas"][0]
            distances = raw_results["distances"][0]
            ids = raw_results["ids"][0]

            for i, (doc, metadata, distance, doc_id) in enumerate(zip(documents, metadatas, distances, ids)):
                formatted.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": metadata,
                    "score": 1.0 - distance,
                    "rank": i + 1,
                    "source": metadata.get("source", "unknown"),
                    "modality": metadata.get("modality", "text"),
                })

        retrieved_docs = formatted
        logger.info(f"[RETRIEVAL] Retrieved {len(retrieved_docs)} chunks from all documents in scope")

        # Apply threshold
        filtered = [
            d for d in retrieved_docs
            if d["score"] >= settings.similarity_threshold
        ]

        logger.info(f"[RETRIEVAL] After threshold filter: {len(filtered)} chunks")

        state["retrieved_documents"] = filtered
        state["evidence_scores"] = [doc.get("score", 0.0) for doc in filtered]

        return state


# 🔑 exported symbol expected by graph_builder
retrieval = RetrievalNode().run
