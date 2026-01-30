"""
Confidence scoring for evidence
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Score confidence in evidence for reasoning"""

    def __init__(self):
        self.threshold_high = 0.8
        self.threshold_medium = 0.5

    def score_evidence(self, evidence: List[Dict[str, Any]]) -> float:
        """
        Score confidence in evidence
        
        Args:
            evidence: List of evidence items with metadata
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            if not evidence:
                return 0.0

            scores = []
            for item in evidence:
                # Base score on similarity
                similarity = item.get('similarity', 0.0)
                
                # Adjust for metadata quality
                metadata_quality = self._assess_metadata_quality(item.get('metadata', {}))
                
                # Combined score
                score = (similarity * 0.7) + (metadata_quality * 0.3)
                scores.append(score)

            # Average confidence
            avg_confidence = sum(scores) / len(scores)
            
            logger.debug(f"Calculated confidence: {avg_confidence:.3f} from {len(evidence)} items")
            return avg_confidence

        except Exception as e:
            logger.error(f"Error scoring confidence: {e}")
            return 0.0

    def _assess_metadata_quality(self, metadata: Dict[str, Any]) -> float:
        """Assess quality of metadata"""
        quality_score = 0.5  # Base score
        
        # Check for source information
        if metadata.get('source'):
            quality_score += 0.2
            
        # Check for timestamps
        if metadata.get('timestamp'):
            quality_score += 0.1
            
        # Check for document type
        if metadata.get('type'):
            quality_score += 0.1
            
        # Check for chunk position
        if metadata.get('chunk_index') is not None:
            quality_score += 0.1
            
        return min(quality_score, 1.0)

    def get_confidence_level(self, score: float) -> str:
        """Get confidence level label"""
        if score >= self.threshold_high:
            return "high"
        elif score >= self.threshold_medium:
            return "medium"
        else:
            return "low"
