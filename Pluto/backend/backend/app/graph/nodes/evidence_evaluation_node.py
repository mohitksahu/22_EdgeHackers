from app.reasoning.evidence.evidence_evaluator import evaluate_evidence
from app.graph.state import GraphState
from app.utils.logging_utils import safe_text
import logging

logger = logging.getLogger(__name__)

class EvidenceEvaluationNode:
    """Node C: The Judge (Evidence Evaluation - Modality-Agnostic)"""
    async def run(self, state: GraphState) -> GraphState:
        retrieved_docs = state.get('retrieved_documents', [])
        query = state.get('query', '')
        
        # Log retrieval results with modality breakdown
        logger.info(f"[EVIDENCE] Evaluating {len(retrieved_docs)} retrieved documents")
        
        # Count evidence by modality
        modality_breakdown = {}
        if retrieved_docs:
            for doc in retrieved_docs:
                modality = doc.get('modality', 'unknown')
                modality_breakdown[modality] = modality_breakdown.get(modality, 0) + 1
            
            logger.info(f"[EVIDENCE] Modality breakdown: {modality_breakdown}")
            
            for i, doc in enumerate(retrieved_docs[:3]):  # Log first 3
                content_safe = safe_text(doc.get('content', ''), max_length=80)
                logger.info(f"  Doc {i+1}: score={doc.get('score', 0):.3f}, modality={doc.get('modality')}, content={content_safe}...")
        else:
            logger.warning("[EVIDENCE] No documents retrieved!")
        
        # MODALITY-AGNOSTIC EVALUATION
        # Accept evidence from ANY modality - let the LLM decide relevance
        # No special handling for visual/audio/text - all evidence is equal
        
        if not retrieved_docs:
            logger.info("[EVIDENCE] ZERO evidence - refusing")
            state['confidence_score'] = 0.0
            state['evidence_sufficient'] = False
            return state
        
        # Score the retrieved documents (modality-agnostic)
        score = await evaluate_evidence(retrieved_docs)
        state['confidence_score'] = score
        
        # UNIFORM THRESHOLD: 0.25 for all modalities
        # Lower threshold allows diverse evidence types through
        evidence_threshold = 0.25
        state['evidence_sufficient'] = score > evidence_threshold and len(retrieved_docs) > 0
        
        logger.info(f"[EVIDENCE] Modality-agnostic evaluation: score={score:.3f}, threshold={evidence_threshold}, sufficient={state['evidence_sufficient']}")
        logger.info(f"[EVIDENCE] Evidence from {len(modality_breakdown)} modalities will be passed to LLM for enumeration")
        
        return state
