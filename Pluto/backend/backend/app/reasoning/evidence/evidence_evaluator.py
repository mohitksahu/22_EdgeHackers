"""
Evidence evaluator for assessing retrieved information quality
"""
import logging
from typing import List, Dict, Any, Tuple
from app.reasoning.llm.llama_reasoner import LlamaReasoner

logger = logging.getLogger(__name__)


class EvidenceEvaluator:
    """Evaluates quality and relevance of retrieved evidence"""

    def __init__(self):
        self.llm_client = LlamaReasoner()

    def evaluate_relevance(self, query: str, evidence: List[str]) -> List[Dict[str, Any]]:
        """Evaluate relevance of each evidence piece to the query"""
        evaluations = []

        for i, evidence_text in enumerate(evidence):
            prompt = f"""Rate the relevance of this evidence to the query on a scale of 1-10 (10 being perfectly relevant):

Query: {query}

Evidence: {evidence_text[:500]}...  # Truncate for efficiency

Relevance score (1-10):"""

            try:
                response = self.llm_client.generate_response(prompt, max_tokens=10)
                score = self._extract_score(response)
                evaluations.append({
                    "index": i,
                    "evidence": evidence_text,
                    "relevance_score": score,
                    "is_relevant": score >= 7
                })
            except Exception as e:
                logger.error(f"Failed to evaluate evidence {i}: {e}")
                evaluations.append({
                    "index": i,
                    "evidence": evidence_text,
                    "relevance_score": 5,  # Neutral score on error
                    "is_relevant": True,
                    "error": str(e)
                })

        return evaluations

    def check_sufficiency(self, query: str, evidence: List[str]) -> Dict[str, Any]:
        """Check if evidence is sufficient to answer the query"""
        combined_evidence = "\n".join(evidence)

        prompt = f"""Determine if the provided evidence is sufficient to fully answer this query:

Query: {query}

Evidence: {combined_evidence[:1000]}...

Is the evidence sufficient? (Yes/No/Partial)
If partial or no, what additional information is needed?"""

        try:
            assessment = self.llm_client.generate_response(prompt, max_tokens=200)

            sufficiency = "unknown"
            if "yes" in assessment.lower():
                sufficiency = "sufficient"
            elif "partial" in assessment.lower():
                sufficiency = "partial"
            elif "no" in assessment.lower():
                sufficiency = "insufficient"

            return {
                "sufficiency": sufficiency,
                "assessment": assessment,
                "evidence_count": len(evidence)
            }
        except Exception as e:
            logger.error(f"Failed to check sufficiency: {e}")
            return {
                "sufficiency": "unknown",
                "assessment": "Evaluation failed",
                "evidence_count": len(evidence),
                "error": str(e)
            }

    def detect_conflicts(self, evidence: List[str]) -> List[Dict[str, Any]]:
        """Detect conflicting information in evidence"""
        conflicts = []

        if len(evidence) < 2:
            return conflicts

        for i in range(len(evidence)):
            for j in range(i + 1, len(evidence)):
                prompt = f"""Compare these two pieces of evidence for conflicts:

Evidence 1: {evidence[i][:300]}...
Evidence 2: {evidence[j][:300]}...

Do they conflict? (Yes/No)
If yes, describe the conflict:"""

                try:
                    response = self.llm_client.generate_response(prompt, max_tokens=100)

                    if "yes" in response.lower():
                        conflicts.append({
                            "evidence_indices": [i, j],
                            "conflict_description": response,
                            "severity": "high" if "significant" in response.lower() else "medium"
                        })
                except Exception as e:
                    logger.error(f"Failed to check conflict between {i} and {j}: {e}")

        return conflicts

    def _extract_score(self, response: str) -> int:
        """Extract numerical score from LLM response"""
        import re
        scores = re.findall(r'\b(\d{1,2})\b', response)
        if scores:
            score = int(scores[0])
            return max(1, min(10, score))  # Clamp to 1-10
        return 5  # Default neutral score


async def evaluate_evidence(retrieved_documents: List[Dict[str, Any]]) -> float:
    """
    Evaluate confidence score for retrieved documents
    
    Args:
        retrieved_documents: List of retrieved document dicts
        
    Returns:
        Confidence score between 0 and 1
    """
    import asyncio
    
    if not retrieved_documents:
        logger.warning("No documents to evaluate")
        return 0.0
    
    try:
        # Extract similarity scores (handle missing scores gracefully)
        scores = []
        for doc in retrieved_documents:
            score = doc.get('score') or doc.get('similarity') or 0.4
            scores.append(float(score))
        
        # Calculate average score
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Boost for multiple sources
        if len(retrieved_documents) >= 3:
            avg_score = min(1.0, avg_score * 1.15)
        elif len(retrieved_documents) >= 2:
            avg_score = min(1.0, avg_score * 1.05)
        
        # Special boost for audio modality (self-identification is strong evidence)
        audio_count = sum(1 for doc in retrieved_documents if doc.get('modality') == 'audio')
        if audio_count > 0:
            avg_score = min(1.0, avg_score * 1.1)
            logger.info(f"[EVIDENCE] Audio evidence boost applied ({audio_count} audio docs)")
        
        # Minimum score if any documents retrieved (let LLM decide final answer)
        if len(retrieved_documents) > 0 and avg_score < 0.35:
            avg_score = 0.35
        
        logger.info(f"Evidence evaluation: {avg_score:.3f} from {len(retrieved_documents)} docs (scores: {[f'{s:.2f}' for s in scores[:3]]})")
        return avg_score
        
    except Exception as e:
        logger.error(f"Evidence evaluation failed: {e}")
        # Return 0.3 instead of 0.5 to be more lenient
        return 0.3 if retrieved_documents else 0.0
