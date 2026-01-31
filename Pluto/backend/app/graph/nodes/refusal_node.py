"""
Refusal node for the LangGraph workflow
"""
import logging
import json
from typing import Dict, Any
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


class RefusalNode:
    """Node responsible for generating refusal responses in evidence-gated RAG"""

    def __init__(self):
        pass

    async def run(self, state: GraphState) -> GraphState:
        """Generate structured refusal response when evidence is insufficient"""
        try:
            query = state.get('query', '')
            logger.info(f"Generating refusal for query: {query[:50]}...")

            # Check if gate node already provided a specific refusal explanation
            if state.get('refusal_explanation'):
                refusal_text = state['refusal_explanation']
                logger.info(f"Using gate-provided refusal explanation: {refusal_text[:100]}...")
            # Fallback: if state is missing refusal info but we know it's out of scope, re-query VectorStore
            elif (state.get("is_out_of_scope") or not state.get("is_allowed", True)) and not state.get('refusal_explanation'):
                try:
                    from app.storage.vector_store import VectorStore
                    vs = VectorStore()
                    kb_summary = vs.get_knowledge_catalog()
                    if not kb_summary.get('topics') and not kb_summary.get('concepts'):
                        refusal_text = "No documents are uploaded yet. Please upload documents before asking questions."
                    else:
                        # Fall back to generic message
                        refusal_text = f"I cannot answer the question: '{query}'.\n\nReason: No supporting evidence was found in the knowledge base.\nSuggestion: Please verify that relevant documents are uploaded."
                except Exception as e:
                    logger.error(f"Failed to re-query KB in refusal node: {e}")
                    refusal_text = f"I cannot answer the question: '{query}'.\n\nReason: No supporting evidence was found in the knowledge base.\nSuggestion: Please verify that relevant documents are uploaded."
            elif state.get("is_out_of_scope") or not state.get("is_allowed", True):
                query_topic = state.get('query_topic', 'Unknown')
                query_concepts = state.get('query_concepts', [])
                kb_summary = state.get('knowledge_base_summary', {})
                document_topics = kb_summary.get('topics', [])
                document_concepts = kb_summary.get('concepts', [])
                
                topic_list = ', '.join(document_topics) if document_topics else 'Unknown'
                concept_preview = ', '.join(document_concepts[:10]) if document_concepts else 'Unknown'
                
                refusal_text = (
                    f"I cannot answer the question: '{query}'.\n\n"
                    f"Reason: Topic/Concept Mismatch. Your question is about '{query_topic}' "
                    f"with concepts {query_concepts}, but my current knowledge base only contains:\n"
                    f"  - Topics: {topic_list}\n"
                    f"  - Sample Concepts: {concept_preview}{'...' if len(document_concepts) > 10 else ''}\n\n"
                    f"Suggestion: Please upload documents relevant to '{query_topic}'."
                )
            else:
                refusal_text = (
                    f"I cannot answer the question: '{query}'.\n\n"
                    f"Reason: No supporting evidence was found in the knowledge base.\n"
                    f"Suggestion: Please verify that relevant documents are uploaded."
                )

            return {
                **state,
                "final_response": refusal_text,
                "status": "refused"
            }

        except Exception as e:
            logger.error(f"Refusal generation failed: {e}")
            state['final_response'] = "Unable to process query due to insufficient evidence."
            state['confidence_score'] = 0.0
            state['cited_sources'] = []
            return state
