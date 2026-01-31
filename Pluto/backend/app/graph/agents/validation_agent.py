"""
Validation Agent - Validates evidence quality and relevance
"""
import logging
from typing import Dict, Any, List

from app.graph.agents.base_agent import BaseAgent, AgentResponse
from app.reasoning.evidence.evidence_evaluator import EvidenceEvaluator
from app.reasoning.conflict.detector import ConflictDetector
from app.config import settings

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """
    Agent responsible for validating retrieved evidence
    - Checks relevance to query
    - Detects conflicts between sources
    - Assesses overall evidence quality
    """

    def __init__(self):
        super().__init__(name="validation")
        self.evaluator = EvidenceEvaluator()
        self.conflict_detector = ConflictDetector()

    async def execute(self, state: Dict[str, Any]) -> AgentResponse:
        """
        Validate retrieved evidence
        
        Args:
            state: Workflow state with documents and query
            
        Returns:
            AgentResponse with validation results
        """
        self.log_execution("Starting evidence validation")
        
        query = state.get('query', '')
        evidence = state.get('evidence', [])
        documents = state.get('retrieved_documents', [])
        
        if not evidence:
            return AgentResponse(
                success=True,
                data={
                    "validation_passed": False,
                    "evidence_score": 0.0,
                    "validation_reason": "No evidence to validate"
                },
                next_agent="reasoning",
                message="Validation skipped: no evidence"
            )
        
        try:
            # Calculate evidence score
            evidence_score = self._calculate_evidence_score(documents)
            
            # Check for conflicts
            conflicts = []
            if len(evidence) >= 2 and settings.conflict_detection_enabled:
                conflict_result = self.conflict_detector.detect_conflicts(query, evidence)
                conflicts = conflict_result.get('conflicts', [])
            
            # Determine if evidence passes threshold
            validation_passed = evidence_score >= settings.confidence_threshold
            
            # Adjust for conflicts
            if conflicts:
                conflict_penalty = len(conflicts) * 0.1
                evidence_score = max(0.0, evidence_score - conflict_penalty)
                validation_passed = evidence_score >= settings.confidence_threshold
            
            self.log_execution(
                "Validation complete",
                {
                    "score": evidence_score,
                    "passed": validation_passed,
                    "conflicts": len(conflicts)
                }
            )
            
            return AgentResponse(
                success=True,
                data={
                    "validation_passed": validation_passed,
                    "evidence_score": evidence_score,
                    "conflict_count": len(conflicts),
                    "conflicts": conflicts,
                    "validation_reason": self._get_validation_reason(
                        evidence_score, validation_passed, conflicts
                    )
                },
                next_agent="reasoning" if validation_passed else "response",
                message=f"Evidence score: {evidence_score:.2f}",
                confidence=evidence_score
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return AgentResponse(
                success=False,
                data={
                    "error": str(e),
                    "validation_passed": False,
                    "evidence_score": 0.0
                },
                message=f"Validation error: {str(e)}"
            )

    def _calculate_evidence_score(
        self,
        documents: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall evidence quality score"""
        if not documents:
            return 0.0
        
        scores = []
        for doc in documents:
            # Get retrieval score
            score = doc.get('score', doc.get('rrf_score', 0.0))
            
            # Boost for certain modalities
            modality = doc.get('metadata', {}).get('modality', 'text')
            if modality == 'audio':
                score *= 1.1  # Slight boost for audio evidence
            
            scores.append(min(score, 1.0))
        
        # Weighted average favoring top results
        if len(scores) >= 3:
            # Top 3 weighted more heavily
            weighted_score = (scores[0] * 0.4 + scores[1] * 0.3 + scores[2] * 0.3)
        else:
            weighted_score = sum(scores) / len(scores)
        
        # Boost for having multiple relevant documents
        quantity_boost = min(len(documents) / 10, 0.15)
        
        return min(weighted_score + quantity_boost, 1.0)

    def _get_validation_reason(
        self,
        score: float,
        passed: bool,
        conflicts: List[Dict]
    ) -> str:
        """Generate human-readable validation reason"""
        reasons = []
        
        if passed:
            reasons.append(f"Evidence score ({score:.2f}) meets threshold")
        else:
            reasons.append(f"Evidence score ({score:.2f}) below threshold ({settings.confidence_threshold})")
        
        if conflicts:
            reasons.append(f"{len(conflicts)} conflict(s) detected between sources")
        
        return "; ".join(reasons)