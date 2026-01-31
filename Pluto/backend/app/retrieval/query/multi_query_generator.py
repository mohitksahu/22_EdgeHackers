"""
Multi-Query Generator using LLM
"""
import logging
from typing import List
import asyncio

logger = logging.getLogger(__name__)


async def generate_multi_queries(query: str, llama_client) -> List[str]:
    """
    Generate multiple query variations using LLM

    Args:
        query: Original user query
        llama_client: QwenReasoner instance

    Returns:
        List of query variations including the original
    """
    # Check if KB is empty - if so, skip expensive LLM calls
    try:
        from app.storage.vector_store import VectorStore
        vector_store = VectorStore()
        kb_summary = vector_store.get_knowledge_catalog()
        kb_topics = kb_summary.get('topics', [])
        kb_concepts = kb_summary.get('concepts', [])

        if not kb_topics and not kb_concepts:
            logger.info("[MULTI-QUERY] KB is empty - skipping LLM query generation")
            return [query]  # Just return original query
    except Exception as e:
        logger.warning(f"[MULTI-QUERY] Failed to check KB status: {e} - proceeding with generation")

    try:
        prompt = f"""Generate 2 alternative phrasings of this question. Only output the questions, nothing else.

Question: {query}

1.
2."""

        # Run in thread pool since llama_client.generate_response is sync
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            llama_client.generate_response,
            prompt,
            100  # Reduced tokens
        )

        # Parse response - extract only actual questions
        lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
        alternative_queries = []

        for line in lines:
            # Skip meta-text like "Here are", "Alternative", etc.
            skip_phrases = ['here are', 'alternative', 'phrasings', 'following', 'rephrase']
            if any(phrase in line.lower() for phrase in skip_phrases):
                continue
            
            # Remove numbering and formatting
            cleaned = line.strip()
            if cleaned and len(cleaned) > 10:  # Must be substantial
                # Remove leading numbers and dots
                if cleaned[0].isdigit() and '.' in cleaned[:3]:
                    cleaned = cleaned.split('.', 1)[1].strip()
                
                # Remove markdown formatting
                cleaned = cleaned.replace('**', '').replace('*', '')
                
                if cleaned and not any(phrase in cleaned.lower() for phrase in skip_phrases):
                    alternative_queries.append(cleaned)

        # Always include original query first
        all_queries = [query]
        if alternative_queries:
            all_queries.extend(alternative_queries[:2])  # Add up to 2 alternatives

        logger.info(f"Generated {len(all_queries)} query variations")
        return all_queries

    except Exception as e:
        logger.error(f"Failed to generate multi-queries: {e}")
        # Return original query on failure
        return [query]
