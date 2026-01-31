"""
Hybrid Retriever - Multi-modal retrieval with reranking
"""
from typing import List, Dict, Any, Optional
import numpy as np

from app.config import settings
from app.core.logging_config import get_safe_logger
from app.storage.vector_store import VectorStore
from app.embeddings.manager import EmbeddingsManager

logger = get_safe_logger(__name__)


class HybridRetriever:
    """
    Hybrid retriever combining text, image, and audio search
    with MMR reranking for diverse results
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.embeddings_manager = EmbeddingsManager()
        self.default_top_k = 10
        self.mmr_lambda = 0.7  # Balance relevance vs diversity
    
    def retrieve(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = None,
        modalities: List[str] = None,
        min_score: float = None,
        use_mmr: bool = True,
        filters: Dict[str, Any] = None,
        use_multimodal_search: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query text
            session_id: Filter by session
            top_k: Number of results
            modalities: Which modalities to search ('text', 'image', 'audio')
            min_score: Minimum similarity threshold
            use_mmr: Apply MMR reranking
            filters: Additional filters
            use_multimodal_search: Use unified multimodal search (recommended)
            
        Returns:
            Dict with documents, scores, metadata
        """
        top_k = top_k or self.default_top_k
        modalities = modalities or ['text', 'image', 'audio']  # Now includes audio
        min_score = min_score or settings.similarity_threshold
        
        logger.info(f"[SEARCH] Query: '{query[:50]}...' | Modalities: {modalities}")
        
        try:
            # Generate query embedding using CLIP text encoder
            query_embedding = self.embeddings_manager.embed_text(query)
            
            # Convert modalities to vector space names
            vector_spaces = [f"{m}_embedding" for m in modalities]
            
            if use_multimodal_search:
                # Use the new unified multimodal search
                results = self.vector_store.query_multimodal(
                    query_embedding=query_embedding,
                    session_id=session_id,
                    vector_spaces=vector_spaces,
                    n_results=top_k * 2 if use_mmr else top_k,
                    score_threshold=min_score,
                    filters=filters
                )
                
                if results.get('status') != 'success':
                    return {
                        "status": "error",
                        "message": results.get('message', 'Search failed'),
                        "documents": [],
                        "count": 0
                    }
                
                # Format results
                all_results = []
                for idx in range(len(results.get('ids', []))):
                    meta = results['metadatas'][idx]
                    all_results.append({
                        'id': results['ids'][idx],
                        'content': results['documents'][idx],
                        'metadata': meta,
                        'score': results['scores'][idx],
                        'modality': meta.get('modality', 'text'),
                        'source_type': meta.get('source_type', 'unknown'),
                        'matched_spaces': meta.get('matched_spaces', []),
                    })
            else:
                # Legacy: Search each modality separately
                all_results = []
                
                for modality in modalities:
                    vector_name = f"{modality}_embedding"
                    
                    results = self.vector_store.query(
                        query_embedding=query_embedding,
                        session_id=session_id,
                        vector_name=vector_name,
                        n_results=top_k * 2,
                        score_threshold=min_score,
                        filters=filters
                    )
                    
                    if results.get('status') == 'success':
                        for idx, (doc_id, doc, meta, score) in enumerate(zip(
                            results['ids'],
                            results['documents'],
                            results['metadatas'],
                            results['scores']
                        )):
                            all_results.append({
                                'id': doc_id,
                                'content': doc,
                                'metadata': meta,
                                'score': score,
                                'modality': meta.get('modality', modality),
                                'source_type': meta.get('source_type', 'unknown'),
                            })
            
            if not all_results:
                logger.info("[SEARCH] No results found")
                return {
                    "status": "success",
                    "documents": [],
                    "count": 0,
                    "message": "No relevant documents found"
                }
            
            # Sort by score
            all_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Apply MMR reranking for diversity
            if use_mmr and len(all_results) > 1:
                all_results = self._mmr_rerank(
                    results=all_results,
                    query_embedding=query_embedding,
                    top_k=top_k,
                    lambda_param=self.mmr_lambda
                )
            else:
                all_results = all_results[:top_k]
            
            # Format output
            documents = []
            for r in all_results:
                documents.append({
                    'id': r['id'],
                    'content': r['content'],
                    'score': r['score'],
                    'modality': r['modality'],
                    'source_type': r['source_type'],
                    'source_file': r['metadata'].get('source_file', ''),
                    'file_name': r['metadata'].get('file_name', ''),
                    'page_number': r['metadata'].get('page_number'),
                    'document_topic': r['metadata'].get('document_topic', ''),
                    'description': r['metadata'].get('description', ''),
                    'matched_spaces': r.get('matched_spaces', []),
                    'metadata': r['metadata']
                })
            
            logger.info(f"[SEARCH] Found {len(documents)} relevant documents")
            
            return {
                "status": "success",
                "documents": documents,
                "count": len(documents),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"[FAIL] Retrieval failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "documents": [],
                "count": 0
            }
    
    def _mmr_rerank(
        self,
        results: List[Dict],
        query_embedding: List[float],
        top_k: int,
        lambda_param: float
    ) -> List[Dict]:
        """
        Maximal Marginal Relevance reranking
        Balances relevance with diversity
        """
        if len(results) <= 1:
            return results
        
        selected = []
        candidates = results.copy()
        
        # Select first (most relevant)
        selected.append(candidates.pop(0))
        
        while len(selected) < top_k and candidates:
            best_score = -float('inf')
            best_idx = 0
            
            for i, candidate in enumerate(candidates):
                # Relevance score (already have from search)
                relevance = candidate['score']
                
                # Diversity: max similarity to already selected
                max_sim = 0.0
                for sel in selected:
                    # Approximate similarity using score difference
                    sim = 1.0 - abs(candidate['score'] - sel['score'])
                    max_sim = max(max_sim, sim)
                
                # MMR score
                mmr = lambda_param * relevance - (1 - lambda_param) * max_sim
                
                if mmr > best_score:
                    best_score = mmr
                    best_idx = i
            
            selected.append(candidates.pop(best_idx))
        
        return selected
    
    def get_context_for_llm(
        self,
        query: str,
        session_id: str = None,
        max_context_length: int = 4000,
    ) -> Dict[str, Any]:
        """
        Get formatted context for LLM generation
        Includes source attribution for grounding
        """
        results = self.retrieve(
            query=query,
            session_id=session_id,
            top_k=10,
            use_mmr=True,
            use_multimodal_search=True  # Use unified multimodal search
        )
        
        if not results.get('documents'):
            return {
                "context": "",
                "sources": [],
                "has_conflicts": False
            }
        
        context_parts = []
        sources = []
        seen_content = set()
        total_length = 0
        
        for doc in results['documents']:
            content = doc['content']
            
            # Deduplicate
            content_hash = hash(content[:100])
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
            
            # Check length
            if total_length + len(content) > max_context_length:
                break
            
            # Format with source
            source_info = f"[{doc['file_name']}"
            if doc.get('page_number'):
                source_info += f" p.{doc['page_number']}"
            source_info += f" | {doc['modality']}]"
            
            context_parts.append(f"{source_info}\n{content}")
            
            sources.append({
                'file': doc['file_name'],
                'page': doc.get('page_number'),
                'modality': doc['modality'],
                'score': doc['score'],
                'topic': doc.get('document_topic'),
                'matched_spaces': doc.get('matched_spaces', [])
            })
            
            total_length += len(content)
        
        # Check for potential conflicts
        has_conflicts = self._detect_conflicts(results['documents'])
        
        return {
            "context": "\n\n---\n\n".join(context_parts),
            "sources": sources,
            "has_conflicts": has_conflicts,
            "document_count": len(sources)
        }
    
    def _detect_conflicts(self, documents: List[Dict]) -> bool:
        """Detect if documents might have conflicting information"""
        if len(documents) < 2:
            return False
        
        # Check for documents from different sources with similar scores
        sources = set()
        for doc in documents[:5]:  # Check top 5
            source = doc.get('file_name', '')
            if source:
                sources.add(source)
        
        # Multiple sources might have different perspectives
        return len(sources) > 1