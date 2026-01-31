"""
Compatibility Gate Node - Topic and Concept Matching
Binary text-based check before retrieval to prevent semantic overlap hallucinations
"""
import logging
from app.graph.state import GraphState
from app.storage.vector_store import VectorStore
from app.utils.topic_utils import normalize_topic

logger = logging.getLogger(__name__)


class CompatibilityGateNode:
    """
    Binary gate that checks if query topics/concepts exist in knowledge base.
    Prevents retrieval when query is clearly out of scope.
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.llm = None  # Lazy-loaded on first semantic check

    def _get_llm(self):
        """Lazy load LLM only when needed for semantic fallback"""
        if self.llm is None:
            from app.reasoning.llm.llama_reasoner import LlamaReasoner
            self.llm = LlamaReasoner()
        return self.llm

    def check_semantic_relationship(self, query_topic: str, doc_topics: list) -> bool:
        """
        Asks LLM if the topics are related to handle synonyms/typos.
        This is a fallback when strict string matching fails.
        """
        if not query_topic or not doc_topics:
            return False
        
        topics_str = ", ".join(doc_topics)
        prompt = f"""Task: Determine if the Query Topic belongs to the Knowledge Base.
Query Topic: {query_topic}
Knowledge Base Topics: {topics_str}

Is '{query_topic}' related to or a sub-topic of the Knowledge Base? 
Respond with exactly YES or NO."""
        
        try:
            llm = self._get_llm()
            response = llm.generate(prompt=prompt, max_tokens=10, temperature=0.0)
            result = "YES" in response.strip().upper()
            logger.info(f"[GATE] LLM semantic check: '{query_topic}' -> {response.strip()}")
            return result
        except Exception as e:
            logger.error(f"[GATE] Semantic check failed: {e}")
            return False

    async def run(self, state: GraphState) -> GraphState:
        """
        Check if query is compatible with knowledge base using direct catalog matching.

        Uses direct catalog lookup instead of VectorStore.query() safeguards.
        """
        query_text = state.get('query', '')

        try:
            # Get query topic and concepts from state (assumed to be extracted earlier)
            query_topic = normalize_topic(state.get("query_topic", ""))
            query_concepts = [normalize_topic(c) for c in state.get("query_concepts", [])]
            
            # Fetch current Knowledge Catalog from Qdrant
            catalog = self.vector_store.get_knowledge_catalog()
            doc_topics = [normalize_topic(t) for t in catalog["topics"]]
            doc_concepts = [normalize_topic(c) for c in catalog["concepts"]]

            logger.info(f"[GATE] Checking Query Topic: '{query_topic}' against Doc Topics: {doc_topics}")

            # RULE 1: Direct Concept Match (Highest Priority - MOST LENIENT)
            # If ANY query concept appears in KB concepts, allow the query
            # This handles cases like "work done" matching "work" in KB
            for concept in query_concepts:
                # Check exact match or if concept is substring of any KB concept
                for kb_concept in doc_concepts:
                    if concept in kb_concept or kb_concept in concept:
                        logger.info(f"[GATE] Direct concept match: '{concept}' <-> '{kb_concept}'")
                        state["is_allowed"] = True
                        state["gate_reason"] = f"concept_match: {concept}"
                        logger.info("[GATE] Query allowed - routing to retrieval")
                        return state
            
            # Also check if query concepts appear in topic strings
            # (e.g., "work" concept matches "Work and Energy" topic)
            for concept in query_concepts:
                for doc_t in doc_topics:
                    if concept in doc_t.lower():
                        logger.info(f"[GATE] Concept found in topic: '{concept}' in '{doc_t}'")
                        state["is_allowed"] = True
                        state["gate_reason"] = f"concept_in_topic: {concept}"
                        logger.info("[GATE] Query allowed - routing to retrieval")
                        return state

            # RULE 2: Fuzzy Topic Match
            # Does 'Biology' relate to 'Photosynthesis Key Concepts'?
            # We check if one is a substring of the other or overlaps
            for doc_t in doc_topics:
                if query_topic in doc_t or doc_t in query_topic:
                    logger.info(f"[GATE] Fuzzy topic match: {query_topic} <-> {doc_t}")
                    state["is_allowed"] = True
                    state["gate_reason"] = f"fuzzy_topic_match: {query_topic} <-> {doc_t}"
                    logger.info("[GATE] Query allowed - routing to retrieval")
                    return state

            # RULE 3: Semantic Fallback (Smartest)
            # If strict checks fail, ask the LLM (handles "Neuron" -> "Nervous System")
            logger.info("[GATE] No string match found. Attempting semantic fallback...")
            if self.check_semantic_relationship(query_topic, doc_topics):
                logger.info(f"[GATE] Semantic match confirmed by LLM.")
                state["is_allowed"] = True
                state["gate_reason"] = "semantic_match_llm"
                logger.info("[GATE] Query allowed - routing to retrieval")
                return state

            # RULE 4: Refusal
            logger.warning(f"[GATE] Query refused: no_match: query topic '{query_topic}' and concepts {query_concepts} not found in knowledge base topics {doc_topics} or concepts {doc_concepts[:20]}...")
            state["is_allowed"] = False
            state["gate_reason"] = f"no_match: query topic '{query_topic}' and concepts {query_concepts} not found in knowledge base topics {doc_topics} or concepts {doc_concepts}"
            state["refusal_explanation"] = f"Your question about '{query_topic}' is not covered by the uploaded documents."
            state["is_out_of_scope"] = True
            return state

        except Exception as e:
            logger.error(f"[GATE] Failed to check compatibility: {e}")
            # Failure safety: default to refusal
            state['is_allowed'] = False
            state['gate_reason'] = f"compatibility_check_failed: {str(e)}"
            state['refusal_explanation'] = "Unable to verify if your question is within the scope of uploaded documents. Please try rephrasing or check document content."
            state['is_out_of_scope'] = True
            return state


# Singleton instance
compatibility_gate = CompatibilityGateNode()
