"""
Reasoning Agent - Performs evidence-based reasoning
"""
import logging
import json
from typing import Dict, Any, List

from app.graph.agents.base_agent import BaseAgent, AgentResponse
from app.config import settings

logger = logging.getLogger(__name__)


REASONING_PROMPT = """You are a reasoning agent in a RAG system. Your task is to analyze the provided evidence and synthesize an answer to the user's question.

EVIDENCE:
{evidence}

USER QUESTION:
{query}

INSTRUCTIONS:
1. Only use information from the provided evidence
2. If evidence is insufficient, say so explicitly
3. Cite which evidence pieces support your answer
4. Express uncertainty when appropriate

Provide your analysis in this JSON format:
{{
    "reasoning": "Your step-by-step reasoning process",
    "key_findings": ["Finding 1", "Finding 2"],
    "answer": "Your synthesized answer based on evidence",
    "confidence": 0.0-1.0,
    "evidence_used": [0, 1, 2],
    "limitations": "Any limitations or gaps in the evidence"
}}

OUTPUT ONLY VALID JSON:"""


class ReasoningAgent(BaseAgent):
    """
    Agent responsible for evidence-based reasoning and answer synthesis
    """

    def __init__(self):
        super().__init__(name="reasoning")

    async def execute(self, state: Dict[str, Any]) -> AgentResponse:
        """
        Perform reasoning over retrieved evidence
        
        Args:
            state: Workflow state with evidence and query
            
        Returns:
            AgentResponse with reasoning results
        """
        self.log_execution("Starting evidence-based reasoning")
        
        query = state.get('query', '')
        evidence = state.get('evidence', [])
        documents = state.get('retrieved_documents', [])
        
        if not evidence:
            return AgentResponse(
                success=False,
                data={"error": "No evidence available for reasoning"},
                next_agent="response",
                message="Cannot reason without evidence"
            )
        
        try:
            # Format evidence for prompt
            formatted_evidence = self._format_evidence(evidence, documents)
            
            # Build reasoning prompt
            prompt = REASONING_PROMPT.format(
                evidence=formatted_evidence,
                query=query
            )
            
            # Generate reasoning
            response = self.llm.generate(
                prompt=prompt,
                max_tokens=800,
                temperature=0.1
            )
            
            # Parse response
            reasoning_result = self._parse_json_response(response)
            
            if not reasoning_result:
                # Fallback: use response as-is
                reasoning_result = {
                    "reasoning": "Direct response from evidence",
                    "answer": response.strip(),
                    "confidence": 0.5,
                    "evidence_used": list(range(min(3, len(evidence)))),
                    "limitations": "Structured parsing failed"
                }
            
            self.log_execution(
                "Reasoning complete",
                {"confidence": reasoning_result.get('confidence', 0.0)}
            )
            
            return AgentResponse(
                success=True,
                data={
                    "reasoning_result": reasoning_result,
                    "synthesized_answer": reasoning_result.get('answer', ''),
                    "reasoning_complete": True,
                    "reasoning_confidence": reasoning_result.get('confidence', 0.5)
                },
                next_agent="response",
                message="Reasoning complete",
                confidence=reasoning_result.get('confidence', 0.5)
            )
            
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            return AgentResponse(
                success=False,
                data={
                    "error": str(e),
                    "reasoning_complete": False
                },
                message=f"Reasoning error: {str(e)}"
            )

    def _format_evidence(
        self,
        evidence: List[str],
        documents: List[Dict[str, Any]]
    ) -> str:
        """Format evidence for the reasoning prompt"""
        formatted_parts = []
        
        for i, (text, doc) in enumerate(zip(evidence, documents)):
            source = doc.get('metadata', {}).get('source_file', 'Unknown')
            modality = doc.get('metadata', {}).get('modality', 'text')
            score = doc.get('score', doc.get('rrf_score', 0.0))
            
            formatted_parts.append(
                f"[Evidence {i}] (Source: {source}, Type: {modality}, Score: {score:.2f})\n{text[:500]}"
            )
        
        return "\n\n".join(formatted_parts)