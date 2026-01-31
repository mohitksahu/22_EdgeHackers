"""
Retrieval orchestrator for multimodal search
"""
import logging
from typing import List, Dict, Any, Optional
from app.storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RetrievalOrchestrator:
    """Orchestrates multimodal retrieval across different strategies"""

    def __init__(self):
        self.vector_store = VectorStore()

    def retrieve(self, query: str, top_k: Optional[int] = None, allowed_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Retrieve relevant documents for the query with optional source filtering"""
        try:
            if top_k is None:
                top_k = 10  # Default

            logger.info(f"Retrieving documents for query: {query[:50]}...")

            # Use VectorStore.query with skip_gate=True since gate_node already validated
            # This prevents redundant topic extraction for each query variation
            raw_results = self.vector_store.query(
                query_text=query,
                modality="text",
                n_results=top_k,
                skip_gate=True  # Gate already validated main query with LLM fallback
            )

            # Check if query was refused by topic-concept gate
            if raw_results.get("status") == "refused":
                return {
                    "query": query,
                    "results": [],
                    "total_found": 0,
                    "refused": True,
                    "reason": raw_results.get("reason", "Query refused by topic-concept gate"),
                    "query_topic": raw_results.get("query_topic"),
                    "query_concepts": raw_results.get("query_concepts"),
                    "knowledge_base_topics": raw_results.get("knowledge_base_topics", []),
                    "knowledge_base_concepts": raw_results.get("knowledge_base_concepts", [])
                }

            # Query was allowed, format results
            formatted_results = self._format_results(raw_results)

            logger.info(f"Retrieved {len(formatted_results)} documents")

            return {
                "query": query,
                "results": formatted_results,
                "total_found": len(formatted_results),
                "query_topic": raw_results.get("query_topic"),
                "query_concepts": raw_results.get("query_concepts"),
                "match_reason": raw_results.get("match_reason")
            }

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return {
                "query": query,
                "results": [],
                "total_found": 0,
                "error": str(e)
            }

    def _format_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format raw retrieval results from VectorStore"""
        formatted = []

        # Handle refusal case
        if raw_results.get("status") == "refused":
            return formatted

        # Handle success case
        if raw_results.get("status") != "success":
            logger.warning(f"Unexpected query status: {raw_results.get('status')}")
            return formatted

        # Extract data from new VectorStore format
        ids = raw_results.get("ids", [])
        distances = raw_results.get("distances", [])
        metadatas = raw_results.get("metadatas", [])
        documents = raw_results.get("documents", [])

        # Ensure all lists have the same length
        min_length = min(len(ids), len(distances), len(metadatas), len(documents))
        if min_length == 0:
            return formatted

        for i in range(min_length):
            metadata = metadatas[i] if i < len(metadatas) else {}
            formatted.append({
                "id": ids[i] if i < len(ids) else f"unknown_{i}",
                "content": documents[i] if i < len(documents) else "",
                "metadata": metadata,
                "score": 1.0 - distances[i] if i < len(distances) else 0.0,  # Convert distance to similarity score
                "rank": i + 1,
                "source": metadata.get("source", "unknown"),
                "modality": metadata.get("modality", "text")
            })

        return formatted

    def _should_use_lexical_fallback(self, query: str) -> bool:
        """Determine if lexical fallback should be used for this query"""
        query_stripped = query.strip()
        words = query_stripped.split()
        
        # Trigger lexical fallback if:
        # 1. Short query (1-3 words) - likely entity or simple question
        if len(words) <= 3:
            return True
        
        # 2. Query contains capitalized words (likely proper nouns/entities)
        # Check for words that start with capital letter (excluding first word)
        if len(words) > 1:
            capitalized_count = sum(1 for word in words[1:] if word and word[0].isupper())
            if capitalized_count > 0:
                return True
        
        # 3. Definition-style questions ("what is X", "who is X", "explain X")
        query_lower = query_stripped.lower()
        definition_patterns = [
            "what is", "who is", "what are", "who are",
            "explain", "define", "describe",
            "tell me about", "information about"
        ]
        if any(pattern in query_lower for pattern in definition_patterns):
            return True
        
        # For longer, complex queries - don't use lexical fallback
        # Let the system refuse if semantic search failed
        return False

    def _calculate_token_overlap(self, query: str, text: str) -> float:
        """Calculate token overlap ratio between query and text"""
        # Tokenize and normalize
        query_tokens = set(query.lower().split())
        text_tokens = set(text.lower().split())
        
        # Remove common stopwords to focus on meaningful tokens
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
                     'should', 'may', 'might', 'must', 'can', 'about', 'of', 'for', 'in', 
                     'on', 'at', 'to', 'from', 'with', 'by'}
        
        query_tokens = query_tokens - stopwords
        text_tokens = text_tokens - stopwords
        
        if not query_tokens:
            return 0.0
        
        # Calculate overlap ratio
        overlap = len(query_tokens.intersection(text_tokens))
        return overlap / len(query_tokens)

    def _lexical_fallback(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Intelligent lexical fallback with token overlap matching"""
        try:
            logger.info(f"Running intelligent lexical search for: {query}")
            
            # Get all documents from vector store
            all_docs = self.vector_store.get_documents()
            
            if not all_docs.get("documents"):
                return []
            
            query_lower = query.lower().strip()
            query_stripped = query_lower.strip('?.,!"\'')
            matches = []
            
            documents = all_docs["documents"]
            metadatas = all_docs.get("metadatas", [])
            ids = all_docs.get("ids", [])
            
            for i, doc in enumerate(documents):
                doc_lower = doc.lower()
                match_score = 0.0
                
                # Strong signal: exact substring match (for entities like "Locash")
                if query_stripped in doc_lower:
                    match_score = 0.7
                # Medium signal: token overlap for multi-word queries ("Who is Locash?")
                else:
                    overlap = self._calculate_token_overlap(query_stripped, doc_lower)
                    # Only consider if significant overlap (40% threshold)
                    if overlap >= 0.4:
                        match_score = 0.5 + (overlap * 0.2)  # Score: 0.5-0.7 based on overlap
                
                # Only add if we have a meaningful match
                if match_score > 0.0:
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    doc_id = ids[i] if i < len(ids) else f"lexical_{i}"
                    
                    matches.append({
                        "id": doc_id,
                        "content": doc,
                        "metadata": metadata,
                        "score": match_score,
                        "rank": len(matches) + 1,
                        "source": metadata.get("source", "unknown"),
                        "modality": metadata.get("modality", "text")
                    })
            
            # Sort by score (descending) and limit to top_k
            matches.sort(key=lambda x: x["score"], reverse=True)
            matches = matches[:top_k]
            
            # Update ranks after sorting
            for i, match in enumerate(matches):
                match["rank"] = i + 1
            
            logger.info(f"Lexical search found {len(matches)} matches (filtered and ranked)")
            return matches
            
        except Exception as e:
            logger.error(f"Lexical fallback failed: {e}")
            return []

        return formatted

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store"""
        try:
            embeddings = []
            metadatas = []
            ids = []

            for doc in documents:
                # Generate embedding based on modality
                if doc.get("modality") == "text":
                    embedding = self.embedder.encode_text([doc["content"]])[0]
                elif doc.get("modality") == "image":
                    # For images, we'd need to process the image first
                    # This is a placeholder
                    embedding = self.embedder.encode_text([doc.get("caption", doc["content"])])[0]
                else:
                    embedding = self.embedder.encode_text([doc["content"]])[0]

                embeddings.append(embedding.tolist())
                metadatas.append(doc.get("metadata", {}))
                ids.append(doc.get("id", f"doc_{len(ids)}"))

            self.vector_store.add_embeddings(embeddings, metadatas, ids)

            logger.info(f"Added {len(documents)} documents to vector store")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
