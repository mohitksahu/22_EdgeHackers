"""
Compatibility gate node
"""
import logging
from typing import Dict, Any

from app.storage.chromadb.client import ChromaDBClient
from app.utils.topic_utils import topics_match, concepts_match

logger = logging.getLogger(__name__)


class CompatibilityGateNode:
    def __init__(self):
        self.client = ChromaDBClient()

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine Intended Document(s) - STRICT Document Awareness
        """

        query_topic = (state.get("query_topic") or "").lower()
        query_concepts = [c.lower() for c in state.get("query_concepts", [])]
        scope_id = state.get("scope_id")

        logger.info(
            "[GATE] Analyzing query for document selection: topic='%s', concepts=%s, scope=%s",
            query_topic,
            query_concepts,
            scope_id,
        )

        # Get per-document summaries
        doc_summaries = self.client.get_documents_summary(scope_id=scope_id)
        
        if not doc_summaries:
            logger.warning("[GATE] No documents found in scope")
            state["is_allowed"] = False
            state["refusal_reason"] = "No documents are currently uploaded."
            return state

        logger.info(f"[GATE] Found {len(doc_summaries)} documents: {list(doc_summaries.keys())}")

        # Step 1: Determine Intended Document(s)
        intended_docs = []
        query_keywords = set(query_topic.split()) | set(query_concepts)

        for doc_filename, summary in doc_summaries.items():
            doc_topics = set(summary["topics"])
            doc_concepts = set(summary["concepts"])
            
            # Check topic alignment
            topic_match = bool(query_topic and query_topic in doc_topics)
            
            # Check concept alignment
            concept_matches = query_keywords & doc_concepts
            concept_score = len(concept_matches) / len(query_keywords) if query_keywords else 0
            
            # Check filename relevance
            filename_lower = doc_filename.lower()
            filename_match = any(kw in filename_lower for kw in query_keywords)
            
            logger.info(f"[GATE] Doc '{doc_filename}': topics={doc_topics}, concepts={doc_concepts}, topic_match={topic_match}, concept_score={concept_score:.2f}, filename_match={filename_match}")
            
            # Determine if this document is relevant
            is_relevant = (
                topic_match or 
                concept_score > 0.3 or  # At least 30% concept overlap
                filename_match
            )
            
            if is_relevant:
                intended_docs.append({
                    "filename": doc_filename,
                    "topic_match": topic_match,
                    "concept_score": concept_score,
                    "filename_match": filename_match,
                    "summary": summary
                })

        # Step 2: Select Evidence Scope
        if not intended_docs:
            # If no documents match, but there are documents, use all (fallback)
            if doc_summaries:
                logger.warning("[GATE] No clear matches, but documents exist - using all documents as fallback")
                selected_docs = list(doc_summaries.keys())
                state["selected_source_files"] = selected_docs
            else:
                logger.warning("[GATE] Query does not match any document")
                state["is_allowed"] = False
                state["refusal_reason"] = "The uploaded documents do not contain information to answer this question."
                return state
        else:
            # Use all relevant documents
            selected_docs = [d["filename"] for d in intended_docs]
            logger.info(f"[GATE] Using relevant documents: {selected_docs}")
            state["selected_source_files"] = selected_docs

        state["intended_documents"] = selected_docs
        state["is_allowed"] = True
        state["document_summaries"] = doc_summaries
        
        return state


# ✅ THIS is what graph_builder expects
compatibility_gate = CompatibilityGateNode()
