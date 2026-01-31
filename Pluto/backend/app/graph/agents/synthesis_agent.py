"""
Synthesis Agent - Generates final responses with conflict handling
"""
from typing import Dict, Any, List, Optional

from app.core.logging_config import get_safe_logger
from app.reasoning.llm.ollama_reasoner import OllamaReasoner
from app.retrieval.retrievers.hybrid_retriever import HybridRetriever

logger = get_safe_logger(__name__)


class SynthesisAgent:
    """
    Agent responsible for synthesizing final responses
    Handles multiple sources and potential conflicts
    """
    
    def __init__(self):
        self.llm = OllamaReasoner()
        self.retriever = HybridRetriever()
    
    def synthesize(
        self,
        query: str,
        session_id: str,
        chat_history: List[Dict] = None,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a synthesized response for the query
        
        Args:
            query: User's question
            session_id: Session identifier
            chat_history: Previous conversation
            include_sources: Whether to include source citations
            
        Returns:
            Dict with response, sources, confidence
        """
        logger.info(f"[SYNTHESIS] Processing: {query[:50]}...")
        
        try:
            # Retrieve relevant context
            context_data = self.retriever.get_context_for_llm(
                query=query,
                session_id=session_id,
                max_context_length=4000
            )
            
            context = context_data.get('context', '')
            sources = context_data.get('sources', [])
            has_conflicts = context_data.get('has_conflicts', False)
            
            # Handle no context case
            if not context:
                return {
                    "response": "I don't have any relevant information about that in the uploaded documents. Please upload documents related to your question or try a different query.",
                    "sources": [],
                    "confidence": 0.0,
                    "has_context": False
                }
            
            # Generate response
            result = self.llm.generate_with_context(
                query=query,
                context=context,
                sources=sources,
                has_conflicts=has_conflicts,
                chat_history=chat_history
            )
            
            response_text = result.get('response', '')
            
            # Add source citations if requested
            if include_sources and sources:
                response_text = self._add_source_citations(response_text, sources)
            
            # Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(sources, result.get('is_grounded', True))
            
            logger.info(f"[SYNTHESIS] Generated response (confidence: {confidence:.2f})")
            
            return {
                "response": response_text,
                "sources": sources,
                "confidence": confidence,
                "has_context": True,
                "has_conflicts": has_conflicts,
                "document_count": len(sources)
            }
            
        except Exception as e:
            logger.error(f"[FAIL] Synthesis failed: {e}")
            return {
                "response": f"I encountered an error processing your question: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _add_source_citations(
        self,
        response: str,
        sources: List[Dict]
    ) -> str:
        """Add source citations to response"""
        if not sources:
            return response
        
        # Group sources by file
        source_summary = {}
        for s in sources:
            file = s.get('file', 'Unknown')
            if file not in source_summary:
                source_summary[file] = {
                    'pages': set(),
                    'modalities': set(),
                    'score': s.get('score', 0)
                }
            if s.get('page'):
                source_summary[file]['pages'].add(s['page'])
            source_summary[file]['modalities'].add(s.get('modality', 'text'))
        
        # Build citation text
        citation_parts = ["\n\n**Sources:**"]
        for file, info in source_summary.items():
            pages = sorted(info['pages'])
            modalities = ', '.join(info['modalities'])
            if pages:
                citation_parts.append(f"- {file} (pages: {', '.join(map(str, pages))}) [{modalities}]")
            else:
                citation_parts.append(f"- {file} [{modalities}]")
        
        return response + '\n'.join(citation_parts)
    
    def _calculate_confidence(
        self,
        sources: List[Dict],
        is_grounded: bool
    ) -> float:
        """Calculate confidence score for the response"""
        if not sources:
            return 0.0
        
        # Base confidence on retrieval scores
        avg_score = sum(s.get('score', 0) for s in sources) / len(sources)
        
        # Adjust based on number of sources
        source_bonus = min(len(sources) / 5, 0.2)  # Up to 0.2 bonus
        
        # Penalty if not grounded
        grounding_penalty = 0 if is_grounded else 0.3
        
        confidence = avg_score + source_bonus - grounding_penalty
        return max(0.0, min(1.0, confidence))