from typing import TypedDict, List, Dict, Annotated, Optional
import operator

class GraphState(TypedDict, total=False):
    query: str                       # User's original input
    query_topic: str                 # Topic classification of the query (e.g., 'AI Systems', 'Biology')
    query_concepts: List[str]        # Specific concepts/nouns extracted from query (e.g., ['carbon dioxide', 'chlorophyll'])
    is_allowed: bool                 # Gate decision: True if query matches knowledge base topics/concepts
    knowledge_base_summary: Dict     # Summary of available topics and concepts in the knowledge base
    expanded_queries: List[str]      # Queries from Multi-Query Generator
    retrieved_documents: List[Dict]  # Aggregated results from Qdrant (typed for citation mapping)
    final_response: str              # Final answer from Llama 3.1 (plain text)
    confidence_score: float          # Score from confidence_scorer.py
    is_hallucination: bool           # Result from hallucination/detector.py
    cited_sources: List[Dict]        # Sources cited in response
    assumptions: List[str]           # Assumptions made during reasoning (Chakravyuh transparency)
    status: str                      # Response status: "success" | "refused"
    evidence_sufficient: bool        # Whether evidence is sufficient
    
    # Query analysis (for visual/audio/text intent detection)
    query_intent: str                # Intent classification (visual_attribute, audio_content, etc.)
    required_modalities: List[str]   # Required modalities based on intent (image, audio, text)

    # Agentic workflow fields (Chakravyuh 1.0 compliance)
    evidence_scores: List[float]     # Relevance score (0-1) for each retrieved chunk
    evidence_score: float            # Maximum relevance score for gatekeeping
    conflicts: List[str]             # Descriptions of detected contradictions between sources
    is_conflicting: bool             # Flag indicating if contradictions exist
    is_sufficient: bool              # Flag to trigger refusal vs generation (based on evidence quality)
    is_out_of_scope: bool            # Flag indicating query topic mismatch
    document_topics: List[str]       # Available topics in the knowledge base

    # Metadata
    processing_time: float
    model_used: Optional[str]
    timestamp: Optional[str]

    # Session management (for multi-user isolation)
    session_id: Optional[str]        # Unique session identifier for context isolation
    conversation_history: List[Dict] # Previous conversation turns for context