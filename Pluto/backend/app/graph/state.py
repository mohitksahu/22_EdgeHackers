from typing import TypedDict, List, Dict, Optional

class GraphState(TypedDict, total=False):
    # 🔑 SCOPE (CRITICAL)
    scope_ids: List[str]

    # Query
    query: str
    query_topic: str
    query_concepts: List[str]

    # Gate
    is_allowed: bool
    is_out_of_scope: bool
    knowledge_base_summary: Dict

    # Retrieval
    expanded_queries: List[str]
    retrieved_documents: List[Dict]

    # Evidence
    evidence_scores: List[float]
    evidence_score: float
    is_sufficient: bool

    # Conflicts
    conflicts: List[str]
    is_conflicting: bool

    # Output
    final_response: str
    status: str

    # Meta
    model_used: Optional[str]
    timestamp: Optional[str]
