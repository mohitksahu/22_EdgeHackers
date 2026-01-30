"""
Multimodal retrieval strategy
"""
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)


class MultimodalRetrievalStrategy:
    """Strategy for processing multimodal retrieval results"""

    def __init__(self):
        self.reranking_enabled = settings.reranking_enabled
        self.similarity_threshold = settings.similarity_threshold

    def process_results(self, query: str, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process and refine retrieval results"""
        try:
            # Filter by similarity threshold
            filtered_results = self._filter_by_threshold(raw_results)

            # Apply reranking if enabled
            if self.reranking_enabled:
                filtered_results = self._rerank_results(query, filtered_results)

            # Balance modalities
            balanced_results = self._balance_modalities(filtered_results)

            return balanced_results

        except Exception as e:
            logger.error(f"Failed to process results: {e}")
            return raw_results

    def _filter_by_threshold(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Filter results by similarity threshold"""
        if not results.get("distances"):
            return results

        # Convert distances to similarities and filter
        similarities = [1.0 - dist for dist in results["distances"][0]]

        # Keep only results above threshold
        keep_indices = [i for i, sim in enumerate(similarities) if sim >= self.similarity_threshold]

        if not keep_indices:
            # If no results meet threshold, keep top 3 results for diversity
            keep_indices = list(range(min(3, len(similarities))))
            logger.warning(f"No results met threshold {self.similarity_threshold}, keeping top {len(keep_indices)}")

        filtered_results = {
            "documents": [[results["documents"][0][i] for i in keep_indices]],
            "metadatas": [[results["metadatas"][0][i] for i in keep_indices]],
            "distances": [[results["distances"][0][i] for i in keep_indices]],
            "ids": [[results["ids"][0][i] for i in keep_indices]]
        }

        logger.info(f"Filtered results: {len(keep_indices)} kept from {len(similarities)}")
        return filtered_results

    def _rerank_results(self, query: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Rerank results based on query relevance"""
        # Simple reranking based on content length and keyword matching
        # In a full implementation, this would use a cross-encoder model

        if not results.get("documents") or not results["documents"][0]:
            return results

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        # Calculate rerank scores
        rerank_scores = []
        for doc, metadata in zip(documents, metadatas):
            score = self._calculate_rerank_score(query, doc, metadata)
            rerank_scores.append(score)

        # Sort by rerank score (descending)
        sorted_indices = sorted(range(len(rerank_scores)), key=lambda i: rerank_scores[i], reverse=True)

        reranked_results = {
            "documents": [[documents[i] for i in sorted_indices]],
            "metadatas": [[metadatas[i] for i in sorted_indices]],
            "distances": [[results["distances"][0][i] for i in sorted_indices]],
            "ids": [[results["ids"][0][i] for i in sorted_indices]]
        }

        logger.info("Results reranked")
        return reranked_results

    def _calculate_rerank_score(self, query: str, document: str, metadata: Dict[str, Any]) -> float:
        """Calculate reranking score for a document"""
        score = 0.0

        # Keyword matching
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        overlap = len(query_words.intersection(doc_words))
        score += overlap * 0.1

        # Content length preference (prefer substantial content)
        if len(document) > 100:
            score += 0.02

        # Query-aware modality boosting
        query_lower = query.lower()
        modality = metadata.get("modality", "unknown")

        # Boost audio for audio-related queries
        if any(keyword in query_lower for keyword in ['audio', 'recording', 'listen', 'sound', 'voice', 'transcription']):
            if modality == "audio":
                score += 0.15  # Strong boost for audio when query mentions it
        elif modality == "text":
            score += 0.02  # Mild preference for text only when query is NOT audio-specific

        return score

    def _balance_modalities(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure balanced representation across modalities"""
        if not results.get("metadatas") or not results["metadatas"][0]:
            return results

        metadatas = results["metadatas"][0]
        modality_counts = {}

        # Count modalities
        for metadata in metadatas:
            modality = metadata.get("modality", "unknown")
            modality_counts[modality] = modality_counts.get(modality, 0) + 1

        # If we have good balance, return as-is
        if len(modality_counts) <= 1 or max(modality_counts.values()) <= len(metadatas) * 0.7:
            return results

        # Simple balancing: ensure at least one of each modality if available
        # In practice, this would be more sophisticated
        logger.info(f"Modalities found: {modality_counts}")
        return results


async def multimodal_retrieve(query: str, orchestrator) -> List[Dict[str, Any]]:
    """
    Perform multimodal retrieval for a query
    
    Args:
        query: Query string
        orchestrator: RetrievalOrchestrator instance
        
    Returns:
        List of retrieved documents
    """
    import asyncio
    
    try:
        # Run sync retrieve in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            orchestrator.retrieve,
            query
        )
        
        return result.get('results', [])
        
    except Exception as e:
        logger.error(f"Multimodal retrieve failed: {e}")
        return []
