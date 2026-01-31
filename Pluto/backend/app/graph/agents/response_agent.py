
"""
Response Agent - Generates final response to user
"""
import logging
import json
from typing import Dict, Any, Optional, List

from app.graph.agents.base_agent import BaseAgent, AgentResponse
from app.reasoning.llm.prompt_builder import build_multimodal_prompt
from app.config import settings

logger = logging.getLogger(__name__)


class ResponseAgent(BaseAgent):
    """
    Agent responsible for generating the final user response
    Handles both successful answers and appropriate refusals
    """

    def __init__(self):
        super().__init__(name="response")

    async def execute(self, state: Dict[str, Any]) -> AgentResponse:
        """
        Generate final response based on workflow results
        
        Args:
            state: Complete workflow state
            
        Returns:
            AgentResponse with final answer
        """
        self.log_execution("Generating final response")
        
        # Check if we should refuse
        validation_passed = state.get('validation_passed', False)
        evidence_score = state.get('evidence_score', 0.0)
        reasoning_result = state.get('reasoning_result', {})
        documents = state.get('retrieved_documents', [])
        query = state.get('query', '')
        
        # Decide response type
        if not documents or evidence_score < settings.refusal_threshold:
            response = self._generate_refusal(query, state)
        elif not validation_passed:
            response = self._generate_low_confidence_response(query, state, reasoning_result)
        else:
            response = self._generate_confident_response(query, state, reasoning_result)
        
        self.log_execution(
            "Response generated",
            {"type": response.get('response_type', 'unknown')}
        )
        
        return AgentResponse(
            success=True,
            data={
                "final_response": response,
                "workflow_complete": True
            },
            next_agent=None,
            message="Response generated successfully",
            confidence=response.get('confidence', 0.0)
        )

    def _generate_refusal(
        self,
        query: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a refusal response"""
        reason = "insufficient_evidence"
        
        if not state.get('retrieved_documents'):
            reason = "no_relevant_documents"
        elif state.get('evidence_score', 0.0) < settings.refusal_threshold:
            reason = "low_evidence_score"
        
        return {
            "refusal": True,
            "response_type": "refusal",
            "reason": reason,
            "answer": self._get_refusal_message(query, reason),
            "confidence": 0.0,
            "cited_sources": []
        }

    def _generate_low_confidence_response(
        self,
        query: str,
        state: Dict[str, Any],
        reasoning_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response with uncertainty notice"""
        answer = reasoning_result.get('answer', '')
        confidence = state.get('evidence_score', 0.3)
        
        # Add uncertainty notice
        uncertainty_notice = (
            "⚠️ Note: This response is based on limited evidence and should be "
            "treated with caution. "
        )
        
        return {
            "refusal": False,
            "response_type": "low_confidence",
            "answer": uncertainty_notice + answer,
            "confidence": confidence,
            "reasoning": reasoning_result.get('reasoning', ''),
            "limitations": reasoning_result.get('limitations', 'Limited evidence available'),
            "cited_sources": self._extract_citations(state)
        }

    def _generate_confident_response(
        self,
        query: str,
        state: Dict[str, Any],
        reasoning_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate confident response"""
        return {
            "refusal": False,
            "response_type": "confident",
            "answer": reasoning_result.get('answer', ''),
            "confidence": reasoning_result.get('confidence', state.get('evidence_score', 0.7)),
            "reasoning": reasoning_result.get('reasoning', ''),
            "key_findings": reasoning_result.get('key_findings', []),
            "cited_sources": self._extract_citations(state)
        }

    def _get_refusal_message(self, query: str, reason: str) -> str:
        """Get appropriate refusal message"""
        messages = {
            "no_relevant_documents": (
                f"I cannot answer your question: \"{query}\"\n\n"
                "The knowledge base does not contain relevant information on this topic. "
                "Please upload documents related to your question or rephrase your query."
            ),
            "low_evidence_score": (
                f"I cannot provide a confident answer to: \"{query}\"\n\n"
                "While some related information was found, the evidence is not strong enough "
                "to formulate a reliable response. Please provide more specific context."
            ),
            "insufficient_evidence": (
                f"I'm unable to answer: \"{query}\"\n\n"
                "The available evidence is insufficient to generate a trustworthy response. "
                "This could be due to missing information or unclear relevance."
            )
        }
        return messages.get(reason, messages["insufficient_evidence"])

    def _extract_citations(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract citation information from state"""
        citations = []
        documents = state.get('retrieved_documents', [])
        
        for doc in documents[:5]:  # Top 5 sources
            metadata = doc.get('metadata', {})
            citations.append({
                "source_id": doc.get('id', 'unknown'),
                "source_file": metadata.get('source_file', 'Unknown'),
                "modality": metadata.get('modality', 'text'),
                "score": doc.get('score', doc.get('rrf_score', 0.0))
            })
        
        return citations