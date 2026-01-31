"""
Retrieval Agent - Handles document retrieval using hybrid search
"""
import logging
from typing import Dict, Any, List

from app.graph.agents.base_agent import BaseAgent, AgentResponse
from app.retrieval.retrievers.hybrid_retriever import HybridRetriever
from app.config import settings

logger = logging.getLogger(__name__)


class RetrievalAgent(BaseAgent):
    """
    Specialized agent for document retrieval
    Uses hybrid retrieval (dense + BM25 + MMR)
    """

    def __init__(self):
        super().__init__(name="retrieval")
        self.retriever = HybridRetriever()

    async def execute(self, state: Dict[str, Any]) -> AgentResponse:
        """
        Execute retrieval for the current query
        
        Args:
            state: Workflow state containing query and session info
            
        Returns:
            AgentResponse with retrieved documents
        """
        self.log_execution("Starting document retrieval")
        
        query = state.get('query', '')
        session_id = state.get('session_id', 'default')
        top_k = state.get('top_k', settings.default_top_k)
        
        if not query:
            return AgentResponse(
                success=False,
                data={"error": "No query provided"},
                message="Retrieval failed: empty query"
            )
        
        try:
            # Perform hybrid retrieval
            results = self.retriever.retrieve(
                query=query,
                session_id=session_id,
                top_k=top_k,
                use_multi_query=settings.multi_query_enabled,
                use_mmr=settings.mmr_enabled,
                use_bm25=settings.bm25_enabled
            )
            
            documents = results.get('results', [])
            
            self.log_execution(
                f"Retrieved {len(documents)} documents",
                {"methods": results.get('retrieval_methods', [])}
            )
            
            # Extract evidence texts
            evidence = [
                doc.get('content', doc.get('text', ''))
                for doc in documents
            ]
            
            return AgentResponse(
                success=True,
                data={
                    "retrieved_documents": documents,
                    "evidence": evidence,
                    "query_variations": results.get('query_variations', [query]),
                    "retrieval_methods": results.get('retrieval_methods', []),
                    "retrieval_attempted": True
                },
                next_agent="validation",
                message=f"Retrieved {len(documents)} documents",
                confidence=self._calculate_retrieval_confidence(documents)
            )
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return AgentResponse(
                success=False,
                data={
                    "error": str(e),
                    "retrieval_attempted": True,
                    "retrieved_documents": []
                },
                message=f"Retrieval error: {str(e)}"
            )

    def _calculate_retrieval_confidence(
        self,
        documents: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence based on retrieval results"""
        if not documents:
            return 0.0
        
        # Average score of top documents
        scores = [doc.get('score', doc.get('rrf_score', 0.5)) for doc in documents[:5]]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Boost for multiple documents
        quantity_boost = min(len(documents) / 10, 0.2)
        
        # Boost for hybrid methods used
        if any('+' in doc.get('retrieval_method', '') for doc in documents):
            method_boost = 0.1
        else:
            method_boost = 0.0
        
        confidence = min(avg_score + quantity_boost + method_boost, 1.0)
        return confidence