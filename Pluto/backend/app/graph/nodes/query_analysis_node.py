from app.reasoning.llm.llama_reasoner import LlamaReasoner
from app.retrieval.query.multi_query_generator import generate_multi_queries
from app.graph.state import GraphState
import logging

logger = logging.getLogger(__name__)

class QueryAnalysisNode:
    """Node A: The Strategist (Query Analysis)"""
    def __init__(self):
        self.llama_client = LlamaReasoner()

    async def run(self, state: GraphState) -> GraphState:
        query = state.get('query', '')

        # Step 0: Check if KB is empty - if so, skip expensive LLM calls
        try:
            from app.storage.vector_store import VectorStore
            vector_store = VectorStore()
            kb_summary = vector_store.get_knowledge_catalog()
            kb_topics = kb_summary.get('topics', [])
            kb_concepts = kb_summary.get('concepts', [])

            if not kb_topics and not kb_concepts:
                logger.info("[ANALYSIS] KB is empty - skipping LLM analysis")
                # Set minimal defaults without LLM calls
                query_words = query.split()[:2]
                state['query_topic'] = ' '.join(query_words).title() if query_words else 'Unknown'
                state['query_concepts'] = [word.lower() for word in query.split()[:3] if len(word) > 2]
                state['expanded_queries'] = [query]  # Just use original query
                return state
        except Exception as e:
            logger.warning(f"[ANALYSIS] Failed to check KB status: {e} - proceeding with analysis")

        # Step 1: Extract both topic and concepts with STRICT formatting
        analysis_prompt = f"""Extract the TOPIC (1-3 words) and KEY CONCEPTS (important nouns/entities) from this question.

Format:
Topic: [topic name]
Concepts: [concept1, concept2, concept3]

Examples:
Question: "What is photosynthesis?" → Topic: Photosynthesis | Concepts: photosynthesis, plants, energy
Question: "How does carbon dioxide affect plants?" → Topic: Plant Biology | Concepts: carbon dioxide, plants, CO2, gas exchange
Question: "Explain machine learning algorithms" → Topic: Machine Learning | Concepts: algorithms, AI, training, models

Question: {query}
Output:"""

        try:
            from app.utils.topic_utils import clean_llm_topic_response, extract_concepts_from_text

            analysis_response = self.llama_client.generate(
                prompt=analysis_prompt,
                max_tokens=50,
                temperature=0.0,
                stop_sequences=["\n\n", "Question:", "Example"]
            )

            # Parse topic and concepts from response
            query_topic = "Unknown"
            query_concepts = []

            lines = analysis_response.strip().split('|')
            for line in lines:
                line = line.strip()
                if line.lower().startswith('topic:'):
                    query_topic = clean_llm_topic_response(line.replace('Topic:', '').replace('topic:', '').strip())
                elif line.lower().startswith('concepts:'):
                    concepts_str = line.replace('Concepts:', '').replace('concepts:', '').strip()
                    query_concepts = [c.strip().lower() for c in concepts_str.split(',') if c.strip()]

            # Fallback: extract from query directly if LLM failed
            if not query_topic or len(query_topic) < 3:
                query_words = query.split()[:3]
                query_topic = ' '.join(query_words).title()

            if not query_concepts:
                query_concepts = extract_concepts_from_text(query)

            logger.info(f"[ANALYSIS] Topic: '{query_topic}', Concepts: {query_concepts}")
            state['query_topic'] = query_topic
            state['query_concepts'] = query_concepts

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            query_words = query.split()[:2]
            state['query_topic'] = ' '.join(query_words).title()
            state['query_concepts'] = extract_concepts_from_text(query)

        # Step 2: Use Llama to generate multiple queries
        expanded_queries = await generate_multi_queries(query, self.llama_client)
        state['expanded_queries'] = expanded_queries
        return state
