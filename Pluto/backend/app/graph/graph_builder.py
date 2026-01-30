"""
LangGraph builder for multimodal RAG workflow
"""
import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph
from langgraph.constants import END
from langchain_core.messages import HumanMessage, AIMessage


from app.graph.state import GraphState
from app.graph.nodes.query_analysis_node import QueryAnalysisNode
from app.graph.nodes.retrieval_node import RetrievalNode
from app.graph.nodes.gate_node import compatibility_gate
from app.graph.nodes.evidence_evaluation_node import EvidenceEvaluationNode
from app.graph.nodes.evidence_grader_node import evidence_grader
from app.graph.nodes.conflict_detector_node import conflict_detector
from app.graph.nodes.generation_node import GenerationNode
from app.graph.nodes.refusal_node import RefusalNode

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builder for the multimodal RAG LangGraph"""

    def __init__(self):
        self.graph: Optional[StateGraph] = None
        self.nodes = {}
        self._initialize_nodes()

    def _initialize_nodes(self):
        """Initialize all graph nodes"""
        self.nodes = {
            "query_analysis": QueryAnalysisNode(),
            "compatibility_gate": compatibility_gate,  # Topic-Concept compatibility check
            "retrieval": RetrievalNode(),
            "evidence_grader": evidence_grader,  # GPU-accelerated evidence grading
            "conflict_detector": conflict_detector,  # GPU-accelerated conflict detection
            "evidence_evaluation": EvidenceEvaluationNode(),  # Legacy confidence scoring
            "generation": GenerationNode(),
            "refusal": RefusalNode(),
        }

    def build_graph(self):
        """Build the complete LangGraph workflow"""
        # Create graph with state
        self.graph = StateGraph(GraphState)

        # Sanity check for type checkers / runtime
        assert self.graph is not None, "StateGraph initialization failed"

        # Add nodes

        # Add nodes (all use async .run method)
        for node_name, node_instance in self.nodes.items():
            self.graph.add_node(node_name, node_instance.run)

        # Define edges
        self._define_edges()

        # Set entry point
        self.graph.set_entry_point("query_analysis")

        # Compile graph
        compiled_graph = self.graph.compile()

        logger.info("LangGraph workflow built successfully")
        return compiled_graph

    def _define_edges(self):
        """Define the edges between nodes with Chakravyuh 1.0 agentic workflow"""
        if self.graph is None:
            raise RuntimeError("Graph not initialized; call build_graph() first")

        # Step 1: Query Analysis -> Compatibility Gate
        self.graph.add_edge("query_analysis", "compatibility_gate")
        
        # Step 2: Compatibility Gate -> Conditional routing
        self.graph.add_conditional_edges(
            "compatibility_gate",
            self.route_after_gate,
            {
                "retrieval": "retrieval",
                "refusal": "refusal"
            }
        )
        
        # Step 3: Retrieval -> Evidence Grading (filter irrelevant chunks)
        self.graph.add_edge("retrieval", "evidence_grader")
        
        # Step 3: Evidence Grading -> Conditional routing
        # If insufficient evidence (is_sufficient=False), go directly to refusal
        # Otherwise, proceed to conflict detection
        self.graph.add_conditional_edges(
            "evidence_grader",
            self._route_after_grading,
            {
                "conflict_detector": "conflict_detector",
                "refusal": "refusal"
            }
        )
        
        # Step 4: Conflict Detection -> Evidence Evaluation (legacy confidence)
        self.graph.add_edge("conflict_detector", "evidence_evaluation")
        
        # Step 5: Evidence Evaluation -> Conditional routing
        self.graph.add_conditional_edges(
            "evidence_evaluation",
            self.check_evidence_sufficiency,
            {
                "generation": "generation",
                "refusal": "refusal"
            }
        )
        
        # Step 6: Generation/Refusal -> END
        self.graph.add_edge("generation", END)
        self.graph.add_edge("refusal", END)


    def _route_after_grading(self, state: GraphState) -> str:
        """
        Relevance Gatekeeper: Route after evidence grading.
        
        Refuses if:
        1. is_sufficient=False (no documents passed threshold)
        2. Average evidence score < 0.4 (semantic drift - wrong topic)
        
        This prevents hallucinations where CLIP finds "best matches" in irrelevant data.
        """
        is_sufficient = state.get('is_sufficient', False)
        evidence_scores = state.get('evidence_scores', [])
        
        # Calculate average evidence score
        avg_score = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0
        
        # Hard gate: refuse if no documents passed threshold
        if not is_sufficient:
            logger.warning(f"Evidence insufficient after grading (0 docs passed threshold). Routing to refusal.")
            return "refusal"
        
        # Balanced semantic drift gate: refuse if average score is below 0.4
        # This catches topic mismatches while allowing relevant documents through
        if avg_score < 0.4:
            logger.warning(f"Evidence score too low (avg={avg_score:.3f} < 0.4). Topic mismatch detected. Routing to refusal.")
            return "refusal"
        
        logger.info(f"Evidence sufficient (avg score={avg_score:.3f}). Proceeding to conflict detection.")
        return "conflict_detector"

    def route_after_gate(self, state: GraphState) -> str:
        """
        Route after compatibility gate: check if query is allowed.
        """
        if not state.get("is_allowed", True):
            logger.info("[GATE] Query not allowed - routing to refusal")
            return "refusal"
        logger.info("[GATE] Query allowed - routing to retrieval")
        return "retrieval"

    def check_evidence_sufficiency(self, state: GraphState) -> str:
        """
        Gatekeeper edge for hallucination suppression.
        """
        if state["evidence_score"] < 0.4:
            return "refusal"

        if state.get("is_conflicting"):
            return "generation"

        return "generation"

    def get_graph_visualization(self) -> str:
        """Get a text representation of the graph structure"""
        return """
Chakravyuh 1.0 Compliant Multimodal RAG Workflow:

1. Query Analysis -> Detect intent and required modalities
   ↓
2. Retrieval -> Fetch top-K chunks from text/image/audio sources
   ↓
3. Evidence Grader (GPU) -> Score each chunk for relevance (0-1)
   ├── is_sufficient=False -> Refusal Node (no relevant evidence)
   └── is_sufficient=True -> Conflict Detector
   ↓
4. Conflict Detector (GPU) -> Cross-reference sources for contradictions
   ├── Sets is_conflicting=True if conflicts found
   └── Proceeds to Evidence Evaluation
   ↓
5. Evidence Evaluation -> Legacy confidence scoring
   ↓
6. Generation Node (Conflict-Aware)
   ├── is_conflicting=False -> Standard grounded answer
   └── is_conflicting=True -> Multi-interpretation format (both sides)
   ↓
7. END

Refusal Node: "I cannot find enough verified evidence to answer this."
"""
