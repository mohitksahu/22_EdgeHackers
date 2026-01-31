"""
BM25 Retriever - Sparse retrieval using BM25 algorithm
"""
import logging
import math
from typing import List, Dict, Any, Optional
from collections import Counter
import re

from app.config import settings

logger = logging.getLogger(__name__)


class BM25Retriever:
    """
    BM25 (Best Matching 25) sparse retriever for keyword-based search
    Complements dense vector search for hybrid retrieval
    """

    def __init__(
        self,
        k1: float = None,
        b: float = None,
        documents: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize BM25 retriever
        
        Args:
            k1: Term frequency saturation parameter (default from settings)
            b: Document length normalization (default from settings)
            documents: Optional pre-loaded documents
        """
        self.k1 = k1 or settings.bm25_k1
        self.b = b or settings.bm25_b
        
        # Document storage
        self.documents: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.doc_count: int = 0
        
        # Inverted index: term -> {doc_id: term_frequency}
        self.inverted_index: Dict[str, Dict[int, int]] = {}
        
        # Document frequency: term -> number of documents containing term
        self.doc_freq: Dict[str, int] = {}
        
        # IDF cache
        self.idf_cache: Dict[str, float] = {}
        
        if documents:
            self.index_documents(documents)

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into terms
        
        Args:
            text: Input text
            
        Returns:
            List of lowercase tokens
        """
        if not text:
            return []
        
        # Convert to lowercase and extract words
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        
        # Remove stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'it', 'its', 'as', 'if', 'then', 'so', 'than'
        }
        
        tokens = [t for t in tokens if t not in stopwords and len(t) > 1]
        return tokens

    def index_documents(self, documents: List[Dict[str, Any]]):
        """
        Index documents for BM25 retrieval
        
        Args:
            documents: List of document dicts with 'content' and 'id' fields
        """
        logger.info(f"Indexing {len(documents)} documents for BM25")
        
        self.documents = documents
        self.doc_count = len(documents)
        self.doc_lengths = []
        self.inverted_index = {}
        self.doc_freq = {}
        self.idf_cache = {}
        
        total_length = 0
        
        for doc_idx, doc in enumerate(documents):
            content = doc.get('content', doc.get('text', ''))
            tokens = self._tokenize(content)
            
            doc_length = len(tokens)
            self.doc_lengths.append(doc_length)
            total_length += doc_length
            
            # Count term frequencies
            term_counts = Counter(tokens)
            
            # Track unique terms in this document
            unique_terms = set()
            
            for term, freq in term_counts.items():
                # Add to inverted index
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                self.inverted_index[term][doc_idx] = freq
                unique_terms.add(term)
            
            # Update document frequencies
            for term in unique_terms:
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1
        
        # Calculate average document length
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0
        
        # Pre-compute IDF values
        for term, df in self.doc_freq.items():
            self.idf_cache[term] = self._compute_idf(df)
        
        logger.info(f"BM25 index built: {len(self.inverted_index)} unique terms")

    def _compute_idf(self, doc_freq: int) -> float:
        """
        Compute IDF (Inverse Document Frequency) for a term
        
        Args:
            doc_freq: Number of documents containing the term
            
        Returns:
            IDF score
        """
        if doc_freq == 0:
            return 0.0
        
        # Standard BM25 IDF formula
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

    def _score_document(self, query_terms: List[str], doc_idx: int) -> float:
        """
        Calculate BM25 score for a single document
        
        Args:
            query_terms: Tokenized query terms
            doc_idx: Document index
            
        Returns:
            BM25 score
        """
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        
        for term in query_terms:
            if term not in self.inverted_index:
                continue
            
            if doc_idx not in self.inverted_index[term]:
                continue
            
            # Get term frequency in document
            tf = self.inverted_index[term][doc_idx]
            
            # Get IDF
            idf = self.idf_cache.get(term, 0.0)
            
            # BM25 scoring formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
            
            score += idf * (numerator / denominator)
        
        return score

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents using BM25
        
        Args:
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum score threshold
            
        Returns:
            List of document dicts with scores
        """
        if not self.documents:
            logger.warning("BM25 index is empty")
            return []
        
        query_terms = self._tokenize(query)
        
        if not query_terms:
            logger.warning("No valid query terms after tokenization")
            return []
        
        # Score all documents
        scores = []
        for doc_idx in range(self.doc_count):
            score = self._score_document(query_terms, doc_idx)
            if score > score_threshold:
                scores.append((doc_idx, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        results = []
        for doc_idx, score in scores[:top_k]:
            doc = self.documents[doc_idx].copy()
            doc['bm25_score'] = score
            doc['retrieval_method'] = 'bm25'
            results.append(doc)
        
        logger.info(f"BM25 retrieved {len(results)} documents for query: {query[:50]}...")
        return results

    def get_term_stats(self, term: str) -> Dict[str, Any]:
        """Get statistics for a specific term"""
        return {
            "term": term,
            "document_frequency": self.doc_freq.get(term, 0),
            "idf": self.idf_cache.get(term, 0.0),
            "in_index": term in self.inverted_index
        }

    def get_index_stats(self) -> Dict[str, Any]:
        """Get overall index statistics"""
        return {
            "document_count": self.doc_count,
            "unique_terms": len(self.inverted_index),
            "average_doc_length": self.avg_doc_length,
            "k1": self.k1,
            "b": self.b
        }