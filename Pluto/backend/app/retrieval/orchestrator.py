"""
Retrieval orchestrator for multimodal search
"""
import logging
from typing import List, Dict, Any, Optional

from app.embeddings.models.multimodal_embedder import MultimodalEmbedder
from app.storage.chromadb.client import ChromaDBClient
from app.retrieval.strategies.multimodal_strategy import MultimodalRetrievalStrategy

logger = logging.getLogger(__name__)


class RetrievalOrchestrator:
    """Orchestrates multimodal retrieval across different strategies"""

    def __init__(self):
        self.embedder = MultimodalEmbedder()
        self.vector_store = ChromaDBClient()
        self.strategy = MultimodalRetrievalStrategy()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            top_k = top_k or 10

            logger.info(f"[RETRIEVAL] Query: {query[:60]}")

            # Embed query
            query_embedding = self.embedder.encode_text([query])[0]

            # 🔑 Scope filtering happens HERE
            raw_results = self.vector_store.query_documents(
                query_embedding=query_embedding,
                n_results=top_k,
                where=where,
            )

            processed = self.strategy.process_results(query, raw_results)
            formatted = self._format_results(processed)

            return {
                "query": query,
                "results": formatted,
                "total_found": len(formatted),
                "strategy_used": "semantic",
            }

        except Exception as e:
            logger.exception("Retrieval failed")
            return {
                "query": query,
                "results": [],
                "total_found": 0,
                "error": str(e),
            }

    # ------------------------------------------------------------------
    # Helpers (UNCHANGED LOGIC, ONLY CLEANED)
    # ------------------------------------------------------------------

    def _format_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        formatted: List[Dict[str, Any]] = []

        if not raw_results or not raw_results.get("documents"):
            return formatted

        documents = raw_results["documents"][0]
        metadatas = raw_results["metadatas"][0]
        distances = raw_results["distances"][0]
        ids = raw_results["ids"][0]

        for i, (doc, metadata, distance, doc_id) in enumerate(
            zip(documents, metadatas, distances, ids)
        ):
            formatted.append(
                {
                    "id": doc_id,
                    "content": doc,
                    "metadata": metadata,
                    "score": 1.0 - distance,
                    "rank": i + 1,
                    "source": metadata.get("source", "unknown"),
                    "modality": metadata.get("modality", "text"),
                }
            )

        return formatted

    def _should_use_lexical_fallback(self, query: str) -> bool:
        words = query.strip().split()

        if len(words) <= 3:
            return True

        if len(words) > 1 and any(w[:1].isupper() for w in words[1:]):
            return True

        q = query.lower()
        return any(
            p in q
            for p in (
                "what is",
                "who is",
                "define",
                "explain",
                "describe",
                "tell me about",
            )
        )

    def _calculate_token_overlap(self, query: str, text: str) -> float:
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be",
            "of", "for", "in", "on", "to", "with", "by",
        }

        q_tokens = set(query.lower().split()) - stopwords
        t_tokens = set(text.lower().split()) - stopwords

        if not q_tokens:
            return 0.0

        return len(q_tokens & t_tokens) / len(q_tokens)

    def _lexical_fallback(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            logger.info("[LEXICAL] Running fallback for query='%s'", query)

            all_docs = self.vector_store.get_documents()
            if not all_docs.get("documents"):
                return []

            matches = []
            q = query.lower().strip("?.!,\"'")

            for i, doc in enumerate(all_docs["documents"]):
                score = 0.0
                doc_l = doc.lower()

                if q in doc_l:
                    score = 0.7
                else:
                    overlap = self._calculate_token_overlap(q, doc_l)
                    if overlap >= 0.4:
                        score = 0.5 + overlap * 0.2

                if score > 0:
                    metadata = all_docs.get("metadatas", [{}])[i]
                    doc_id = all_docs.get("ids", [f"lex_{i}"])[i]

                    matches.append(
                        {
                            "id": doc_id,
                            "content": doc,
                            "metadata": metadata,
                            "score": score,
                            "rank": 0,
                            "source": metadata.get("source", "unknown"),
                            "modality": metadata.get("modality", "text"),
                        }
                    )

            matches.sort(key=lambda x: x["score"], reverse=True)
            matches = matches[:top_k]

            for i, m in enumerate(matches):
                m["rank"] = i + 1

            logger.info("[LEXICAL] Found %d matches", len(matches))
            return matches

        except Exception as e:
            logger.error("[LEXICAL] Failed: %s", e)
            return []

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        try:
            embeddings, metadatas, ids = [], [], []

            for doc in documents:
                embedding = self.embedder.encode_text([doc["content"]])[0]
                embeddings.append(embedding.tolist())
                metadatas.append(doc.get("metadata", {}))
                ids.append(doc.get("id", f"doc_{len(ids)}"))

            self.vector_store.add_embeddings(embeddings, metadatas, ids)
            logger.info("Added %d documents to vector store", len(documents))
            return True

        except Exception as e:
            logger.error("Failed to add documents: %s", e)
            return False
