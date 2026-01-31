"""
Multi-Query Retriever - Generates multiple query variations for comprehensive retrieval
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Set

from app.config import settings
from app.reasoning.llm.ollama_reasoner import OllamaReasoner

logger = logging.getLogger(__name__)


class MultiQueryRetriever:
    """
    Generates multiple variations of the user query to improve recall
    Uses LLM to create semantically similar but lexically different queries
    """

    def __init__(self, llm_client: Optional[OllamaReasoner] = None):
        """
        Initialize multi-query retriever
        
        Args:
            llm_client: Optional LLM client for query generation
        """
        self.llm_client = llm_client or OllamaReasoner()
        self.num_queries = settings.multi_query_count

    def generate_queries(self, original_query: str) -> List[str]:
        """
        Generate multiple query variations
        
        Args:
            original_query: Original user query
            
        Returns:
            List of query variations including original
        """
        queries = [original_query]
        
        if not settings.multi_query_enabled:
            return queries
        
        try:
            prompt = f"""Generate {self.num_queries - 1} alternative phrasings of this question.
Each variation should:
- Preserve the original meaning
- Use different words or sentence structure
- Be a complete question

Original question: {original_query}

Output ONLY the alternative questions, one per line, numbered:
1."""

            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            # Parse response
            alternatives = self._parse_query_response(response)
            queries.extend(alternatives)
            
            logger.info(f"Generated {len(queries)} query variations")
            
        except Exception as e:
            logger.error(f"Multi-query generation failed: {e}")
        
        return queries[:self.num_queries]

    async def generate_queries_async(self, original_query: str) -> List[str]:
        """
        Async version of query generation
        
        Args:
            original_query: Original user query
            
        Returns:
            List of query variations
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.generate_queries,
            original_query
        )

    def _parse_query_response(self, response: str) -> List[str]:
        """
        Parse LLM response to extract query variations
        
        Args:
            response: LLM response text
            
        Returns:
            List of parsed queries
        """
        queries = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 2., etc.)
            if line[0].isdigit() and '.' in line[:3]:
                line = line.split('.', 1)[1].strip()
            
            # Remove bullet points
            if line.startswith(('-', '*', '•')):
                line = line[1:].strip()
            
            # Skip meta text
            skip_phrases = [
                'here are', 'alternative', 'variations', 'following',
                'questions:', 'queries:', 'rephrased'
            ]
            if any(phrase in line.lower() for phrase in skip_phrases):
                continue
            
            # Validate it looks like a question
            if len(line) > 10 and not line.startswith('['):
                queries.append(line)
        
        return queries

    def deduplicate_results(
        self,
        all_results: List[List[Dict[str, Any]]],
        key_field: str = 'id'
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate and merge results from multiple queries
        
        Args:
            all_results: List of result lists from each query
            key_field: Field to use for deduplication
            
        Returns:
            Merged and deduplicated results
        """
        seen_ids: Set[str] = set()
        merged_results = []
        score_map: Dict[str, float] = {}
        
        for results in all_results:
            for doc in results:
                doc_id = doc.get(key_field, doc.get('chunk_id', ''))
                
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    merged_results.append(doc)
                    score_map[doc_id] = doc.get('score', 0.0)
                else:
                    # Update score if higher
                    current_score = doc.get('score', 0.0)
                    if current_score > score_map.get(doc_id, 0.0):
                        # Find and update the document
                        for i, existing_doc in enumerate(merged_results):
                            if existing_doc.get(key_field) == doc_id:
                                merged_results[i]['score'] = current_score
                                score_map[doc_id] = current_score
                                break
        
        # Sort by score
        merged_results.sort(key=lambda x: x.get('score', 0.0), reverse=True)
        
        logger.info(f"Deduplicated {sum(len(r) for r in all_results)} results to {len(merged_results)}")
        return merged_results

    def expand_query_with_context(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Expand query using conversation context
        
        Args:
            query: Current query
            chat_history: Previous conversation turns
            
        Returns:
            Expanded query with context
        """
        if not chat_history:
            return query
        
        try:
            # Build context from recent history
            context_parts = []
            for turn in chat_history[-3:]:  # Last 3 turns
                if 'user_query' in turn:
                    context_parts.append(f"User: {turn['user_query']}")
                if 'system_response' in turn:
                    context_parts.append(f"Assistant: {turn['system_response'][:200]}...")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Given this conversation context:
{context}

The user now asks: {query}

Rewrite the current question to be self-contained, resolving any pronouns or references.
Output ONLY the rewritten question, nothing else:"""

            expanded = self.llm_client.generate(
                prompt=prompt,
                max_tokens=100,
                temperature=0.3
            )
            
            if expanded and len(expanded) > 10:
                logger.info(f"Expanded query: '{query}' -> '{expanded}'")
                return expanded.strip()
            
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
        
        return query