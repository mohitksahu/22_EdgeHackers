"""
Evidence Grader Node - GPU Accelerated
Grades the relevance of each retrieved chunk to filter out irrelevant documents before generation.
"""
import logging
from typing import Dict, Any
from app.graph.state import GraphState
from app.reasoning.llm.llama_reasoner import LlamaReasoner

logger = logging.getLogger(__name__)

class EvidenceGrader:
    """Grades retrieved documents for relevance using LLM"""
    
    def __init__(self):
        self.reasoner = LlamaReasoner()
        self.relevance_threshold = 0.5  # Balanced threshold for analytical grounding
        
    def grade_document(self, document: Dict, query: str) -> float:
        """
        Grade a single document for relevance to the query.
        
        Args:
            document: Document dict with 'content', 'source_type', 'metadata'
            query: User's question
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        content = document.get('content', '')
        source_type = document.get('source_type', 'unknown')
        
        # Truncate content to prevent token limit issues
        content = content[:2000]
        
        prompt = f"""Task: Is this document relevant to the question?
Question: {query}
Document: {content}
Respond with only 'YES' or 'NO'."""
        
        try:
            response = self.reasoner.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.0,
                stop_sequences=["\n\n", "Question:"]
            )
            
            # Simple YES/NO parsing (optimized for 1B model)
            response_clean = response.strip().upper()
            is_relevant = 'YES' in response_clean
            
            # Binary scoring: 0.0 for NO, 0.9 for YES
            if is_relevant:
                final_score = 0.9
                logger.debug(f"Graded document from {source_type}: {final_score:.2f} (YES - relevant)")
            else:
                final_score = 0.0
                logger.debug(f"Graded document from {source_type}: {final_score:.2f} (NO - not relevant)")
            
            return final_score
            
        except Exception as e:
            logger.error(f"Error grading document: {e}")
            return 0.5  # Neutral score on error
    
    async def run(self, state: GraphState) -> GraphState:
        """
        Graph-compatible entrypoint.
        Grades all retrieved documents and filters out irrelevant ones.
        
        Sets:
            - evidence_scores: List of relevance scores
            - is_sufficient: Boolean flag (True if at least one doc scores >= threshold)
            - retrieved_documents: Filtered list (only relevant docs)
        """
        query = state.get("query", "")
        documents = state.get("retrieved_documents", [])
        
        logger.info(f"Grading {len(documents)} retrieved documents...")
        
        if not documents:
            logger.warning("No documents to grade. Setting is_sufficient=False")
            state["evidence_scores"] = []
            state["is_sufficient"] = False
            state["retrieved_documents"] = []
            return state
        
        # Grade each document
        evidence_scores = []
        graded_docs = []
        
        for doc in documents:
            score = self.grade_document(doc, query)
            evidence_scores.append(score)
            
            # Keep document if it meets threshold
            if score >= self.relevance_threshold:
                graded_docs.append(doc)
        
        # Calculate statistics
        avg_score = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0
        max_score = max(evidence_scores) if evidence_scores else 0.0
        passed_count = len(graded_docs)
        
        logger.info(f"Evidence grading complete: {passed_count}/{len(documents)} documents passed threshold {self.relevance_threshold}")
        logger.info(f"Scores - Avg: {avg_score:.3f}, Max: {max_score:.3f}")
        
        # Update state
        state["evidence_scores"] = evidence_scores
        state["is_sufficient"] = passed_count > 0  # At least one relevant document
        state["retrieved_documents"] = graded_docs  # Replace with filtered docs
        state["evidence_score"] = max_score
        
        return state


# Singleton instance
evidence_grader = EvidenceGrader()
