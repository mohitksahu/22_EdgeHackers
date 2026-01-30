"""
Conflict detector for identifying contradictory evidence
"""
import logging
from typing import List, Dict, Any, Set
from app.reasoning.llm.llama_reasoner import LlamaReasoner

logger = logging.getLogger(__name__)


class ConflictDetector:
    """Detects conflicts and contradictions in retrieved evidence"""

    def __init__(self):
        self.llm_client = LlamaReasoner()

    def detect_conflicts(self, query: str, evidence: List[str]) -> Dict[str, Any]:
        """Detect conflicts in the evidence set"""
        conflicts = []
        conflict_pairs = []

        # Check pairwise conflicts
        for i in range(len(evidence)):
            for j in range(i + 1, len(evidence)):
                conflict = self._check_pair_conflict(evidence[i], evidence[j])
                if conflict["has_conflict"]:
                    conflicts.append(conflict)
                    conflict_pairs.append((i, j))

        # Analyze overall consistency
        consistency_score = self._calculate_consistency_score(evidence, conflicts)

        return {
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
            "conflict_pairs": conflict_pairs,
            "consistency_score": consistency_score,
            "overall_consistent": consistency_score > 0.8
        }

    def _check_pair_conflict(self, evidence1: str, evidence2: str) -> Dict[str, Any]:
        """Check if two pieces of evidence conflict"""
        prompt = f"""Compare these two pieces of evidence for contradictions or conflicts:

Evidence 1: {evidence1[:400]}...
Evidence 2: {evidence2[:400]}...

Do they contradict each other? (Yes/No)
If yes, explain the contradiction briefly."""

        try:
            response = self.llm_client.generate_response(prompt, max_tokens=100)

            has_conflict = "yes" in response.lower()

            return {
                "has_conflict": has_conflict,
                "evidence_pair": [evidence1, evidence2],
                "explanation": response if has_conflict else None,
                "severity": self._assess_severity(response) if has_conflict else None
            }
        except Exception as e:
            logger.error(f"Failed to check conflict: {e}")
            return {
                "has_conflict": False,
                "evidence_pair": [evidence1, evidence2],
                "error": str(e)
            }

    def _assess_severity(self, conflict_explanation: str) -> str:
        """Assess the severity of a conflict"""
        explanation_lower = conflict_explanation.lower()

        if any(word in explanation_lower for word in ["major", "significant", "fundamental", "opposite"]):
            return "high"
        elif any(word in explanation_lower for word in ["minor", "slight", "partial"]):
            return "medium"
        else:
            return "low"

    def _calculate_consistency_score(self, evidence: List[str], conflicts: List[Dict]) -> float:
        """Calculate overall consistency score"""
        if not evidence:
            return 1.0

        total_pairs = len(evidence) * (len(evidence) - 1) / 2
        if total_pairs == 0:
            return 1.0

        conflict_count = len(conflicts)
        consistency_score = 1.0 - (conflict_count / total_pairs)

        return max(0.0, consistency_score)

    def resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attempt to resolve detected conflicts"""
        resolutions = []

        for conflict in conflicts:
            if conflict["severity"] == "high":
                resolution = self._resolve_high_conflict(conflict)
            else:
                resolution = self._resolve_low_conflict(conflict)

            resolutions.append({
                "conflict": conflict,
                "resolution": resolution
            })

        return resolutions

    def _resolve_high_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve high-severity conflicts"""
        prompt = f"""Two pieces of evidence conflict significantly:

Evidence 1: {conflict['evidence_pair'][0][:300]}...
Evidence 2: {conflict['evidence_pair'][1][:300]}...

Conflict: {conflict['explanation']}

How should this conflict be resolved? Provide a reasoned approach."""

        try:
            resolution = self.llm_client.generate_response(prompt, max_tokens=150)
            return {
                "approach": "manual_review",
                "reasoning": resolution,
                "requires_human": True
            }
        except Exception as e:
            return {
                "approach": "flag_for_review",
                "error": str(e),
                "requires_human": True
            }

    def _resolve_low_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve low-severity conflicts"""
        return {
            "approach": "accept_both",
            "reasoning": "Low-severity conflict can be noted but both pieces retained",
            "requires_human": False
        }
