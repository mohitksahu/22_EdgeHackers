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
    try:
        prompt = f"""Given this user question, generate 2 alternative ways to phrase the same question. The goal is to retrieve relevant documents from different perspectives.

Original question: {query}

Generate 2 alternative phrasings (one per line):
1."""

        # Run in thread pool since llama_client.generate_response is sync
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            llama_client.generate_response,
            prompt,
            150  # max_tokens
        )

        # Parse response
        lines = response.strip().split('\n')
        alternative_queries = []
        
        for line in lines:
            # Clean up numbered lists
            cleaned = line.strip()
            if cleaned and len(cleaned) > 10:  # Filter out too-short fragments
                # Remove numbering if present
                if cleaned[0].isdigit() and '.' in cleaned[:3]:
                    cleaned = cleaned.split('.', 1)[1].strip()
                alternative_queries.append(cleaned)

        # Always include original query
        all_queries = [query] + alternative_queries[:2]  # Limit to 3 total
        
        logger.info(f"Generated {len(all_queries)} query variations")
        return all_queries

    except Exception as e:
        logger.error(f"Failed to generate multi-queries: {e}")
        # Return original query on failure
        return [query]
