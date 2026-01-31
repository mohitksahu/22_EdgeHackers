"""
MMR (Maximal Marginal Relevance) Reranker
Balances relevance and diversity in search results
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class MMRReranker:
    """
    Maximal Marginal Relevance reranker for diversifying search results
    
    MMR = λ * Sim(d, q) - (1-λ) * max(Sim(d, d_selected))
    
    Where:
    - λ (lambda) controls relevance vs diversity tradeoff
    - Sim(d, q) is similarity between document and query
    - Sim(d, d_selected) is similarity to already selected documents
    """

    def __init__(self, lambda_param: float = None):
        """
        Initialize MMR reranker
        
        Args:
            lambda_param: Balance parameter (0=diversity, 1=relevance)
        """
        self.lambda_param = lambda_param or settings.mmr_lambda

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        if vec1 is None or vec2 is None:
            return 0.0
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _compute_similarity_matrix(
        self,
        embeddings: List[np.ndarray]
    ) -> np.ndarray:
        """
        Compute pairwise similarity matrix for all documents
        
        Args:
            embeddings: List of document embeddings
            
        Returns:
            NxN similarity matrix
        """
        n = len(embeddings)
        sim_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i, n):
                sim = self._cosine_similarity(embeddings[i], embeddings[j])
                sim_matrix[i, j] = sim
                sim_matrix[j, i] = sim
        
        return sim_matrix

    def rerank(
        self,
        query_embedding: np.ndarray,
        documents: List[Dict[str, Any]],
        document_embeddings: List[np.ndarray],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using MMR
        
        Args:
            query_embedding: Query vector
            documents: List of document dicts
            document_embeddings: List of document embeddings
            top_k: Number of documents to return
            
        Returns:
            Reranked documents with MMR scores
        """
        if not documents or not document_embeddings:
            return []
        
        if len(documents) != len(document_embeddings):
            logger.error("Document count mismatch with embeddings")
            return documents[:top_k]
        
        n_docs = len(documents)
        top_k = min(top_k, n_docs)
        
        # Compute query-document similarities
        query_sims = np.array([
            self._cosine_similarity(query_embedding, emb)
            for emb in document_embeddings
        ])
        
        # Compute document-document similarity matrix
        doc_sim_matrix = self._compute_similarity_matrix(document_embeddings)
        
        # MMR selection
        selected_indices = []
        remaining_indices = list(range(n_docs))
        
        for _ in range(top_k):
            if not remaining_indices:
                break
            
            mmr_scores = []
            
            for idx in remaining_indices:
                # Relevance component
                relevance = query_sims[idx]
                
                # Diversity component (max similarity to selected docs)
                if selected_indices:
                    diversity_penalty = max(
                        doc_sim_matrix[idx, sel_idx]
                        for sel_idx in selected_indices
                    )
                else:
                    diversity_penalty = 0.0
                
                # MMR score
                mmr = self.lambda_param * relevance - (1 - self.lambda_param) * diversity_penalty
                mmr_scores.append((idx, mmr))
            
            # Select document with highest MMR score
            best_idx, best_score = max(mmr_scores, key=lambda x: x[1])
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        # Build result list
        results = []
        for rank, idx in enumerate(selected_indices):
            doc = documents[idx].copy()
            doc['mmr_score'] = query_sims[idx]
            doc['mmr_rank'] = rank + 1
            doc['retrieval_method'] = doc.get('retrieval_method', 'dense') + '+mmr'
            results.append(doc)
        
        logger.info(f"MMR reranked {len(results)} documents (λ={self.lambda_param})")
        return results

    def rerank_by_scores(
        self,
        documents: List[Dict[str, Any]],
        relevance_scores: List[float],
        document_embeddings: List[np.ndarray],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank using pre-computed relevance scores
        
        Args:
            documents: List of document dicts
            relevance_scores: Pre-computed relevance scores
            document_embeddings: Document embeddings for diversity
            top_k: Number of documents to return
            
        Returns:
            Reranked documents
        """
        if not documents:
            return []
        
        n_docs = len(documents)
        top_k = min(top_k, n_docs)
        
        # Normalize relevance scores
        max_score = max(relevance_scores) if relevance_scores else 1.0
        if max_score > 0:
            norm_scores = [s / max_score for s in relevance_scores]
        else:
            norm_scores = [0.0] * len(relevance_scores)
        
        # Compute diversity matrix
        doc_sim_matrix = self._compute_similarity_matrix(document_embeddings)
        
        # MMR selection
        selected_indices = []
        remaining_indices = list(range(n_docs))
        
        for _ in range(top_k):
            if not remaining_indices:
                break
            
            mmr_scores = []
            
            for idx in remaining_indices:
                relevance = norm_scores[idx]
                
                if selected_indices:
                    diversity_penalty = max(
                        doc_sim_matrix[idx, sel_idx]
                        for sel_idx in selected_indices
                    )
                else:
                    diversity_penalty = 0.0
                
                mmr = self.lambda_param * relevance - (1 - self.lambda_param) * diversity_penalty
                mmr_scores.append((idx, mmr))
            
            best_idx, _ = max(mmr_scores, key=lambda x: x[1])
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        # Build results
        results = []
        for rank, idx in enumerate(selected_indices):
            doc = documents[idx].copy()
            doc['mmr_rank'] = rank + 1
            doc['original_score'] = relevance_scores[idx]
            results.append(doc)
        
        return results