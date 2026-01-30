"""
Refusal engine for handling insufficient evidence and hallucinations
"""
import logging
from typing import Dict, Any, Optional
from app.reasoning.llm.llama_reasoner import LlamaReasoner

logger = logging.getLogger(__name__)


class RefusalEngine:
    """Engine for generating appropriate refusals when evidence is insufficient"""

    def __init__(self):
        self.llm_client = LlamaReasoner()

    def should_refuse(self, query: str, evidence: list, confidence_score: float) -> bool:
        """Determine if the query should be refused based on evidence quality"""
        if not evidence:
            return True

        # Check confidence threshold
        if confidence_score < 0.3:  # Low confidence threshold
            return True

        # Check evidence sufficiency
        sufficiency = self._assess_sufficiency(query, evidence)
        return sufficiency["should_refuse"]

    def generate_refusal(self, query: str, evidence: list, reason: str = "insufficient_evidence") -> str:
        """Generate an appropriate refusal response"""
        if reason == "insufficient_evidence":
            return self._refuse_insufficient_evidence(query, evidence)
        elif reason == "hallucination_risk":
            return self._refuse_hallucination_risk(query)
        elif reason == "conflict":
            return self._refuse_conflict(query)
        else:
            return self._refuse_generic(query)

    def _assess_sufficiency(self, query: str, evidence: list) -> Dict[str, Any]:
        """Assess if evidence is sufficient for the query"""
        evidence_text = "\n".join(evidence[:3])  # Limit to first 3 pieces

        prompt = f"""Evaluate if this evidence is sufficient to answer the query:

Query: {query}

Evidence: {evidence_text[:500]}...

Can this query be answered with confidence using only this evidence? (Yes/No)
If no, why not?"""

        try:
            response = self.llm_client.generate_response(prompt, max_tokens=100)

            should_refuse = "no" in response.lower() or "insufficient" in response.lower()

            return {
                "should_refuse": should_refuse,
                "reasoning": response,
                "evidence_count": len(evidence)
            }
        except Exception as e:
            logger.error(f"Failed to assess sufficiency: {e}")
            return {
                "should_refuse": True,  # Default to refuse on error
                "reasoning": "Assessment failed",
                "error": str(e)
            }

    def _refuse_insufficient_evidence(self, query: str, evidence: list) -> str:
        """Generate refusal for insufficient evidence"""
        evidence_summary = f"{len(evidence)} pieces of evidence" if evidence else "no evidence"

        return f"""I cannot provide a confident answer to your query: "{query}"

Based on the available information ({evidence_summary}), there is insufficient evidence to formulate a reliable response. The retrieved information does not adequately address your question.

Please provide more context or rephrase your question to help me locate more relevant information."""

    def _refuse_hallucination_risk(self, query: str) -> str:
        """Generate refusal for hallucination risk"""
        return f"""I must decline to answer your query: "{query}"

The available evidence, while present, carries a high risk of leading to inaccurate or fabricated information. To maintain reliability, I require more substantial and verifiable evidence before providing an answer."""

    def _refuse_conflict(self, query: str) -> str:
        """Generate refusal for conflicting evidence"""
        return f"""I cannot provide a definitive answer to your query: "{query}"

The retrieved evidence contains conflicting information that cannot be reliably reconciled. This creates uncertainty that would compromise the accuracy of any response.

Please consider refining your query or providing additional context to help resolve these conflicts."""

    def _refuse_generic(self, query: str) -> str:
        """Generate generic refusal"""
        return f"""I'm unable to provide a satisfactory answer to your query: "{query}"

The available evidence does not meet the threshold for generating a reliable response. This could be due to insufficient information, conflicting data, or other quality concerns.

Please try rephrasing your question or providing more specific details."""

    def generate_uncertainty_notice(self, confidence_score: float) -> str:
        """Generate a notice about uncertainty in the response"""
        if confidence_score < 0.5:
            return "⚠️ This response is based on limited evidence and should be treated with caution."
        elif confidence_score < 0.7:
            return "ℹ️ This response has moderate confidence based on the available evidence."
        else:
            return "OK This response is based on strong supporting evidence."
