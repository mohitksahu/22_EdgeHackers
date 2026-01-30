"""
Topic normalization utilities for Topic Gate Architecture
"""
import logging
from typing import List, Set
import re

logger = logging.getLogger(__name__)


def normalize_topic(topic: str) -> str:
    """
    Normalize a topic string for fuzzy matching.
    
    Args:
        topic: Raw topic string
        
    Returns:
        Normalized topic string (lowercase, stripped, single spaces)
    """
    if not topic:
        return ""
    
    # Convert to lowercase
    normalized = topic.lower().strip()
    
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove common articles and prepositions for better matching
    stop_words = ['the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for']
    words = normalized.split()
    filtered_words = [w for w in words if w not in stop_words]
    
    return ' '.join(filtered_words) if filtered_words else normalized


def clean_llm_topic_response(raw_response: str) -> str:
    """
    Clean LLM topic extraction response by removing verbosity.
    
    Handles common LLM patterns like:
    - "The main topic is: Biology"
    - "Topic: Computer Science"
    - "This document is about \"Photosynthesis\"."
    - "Photosynthesis Concepts: -" (hallucination)
    
    Args:
        raw_response: Raw LLM output
        
    Returns:
        Clean topic (1-3 words)
    """
    if not raw_response:
        return ""
    
    cleaned = raw_response.strip()
    
    logger.debug(f"[TOPIC CLEAN] Input: '{cleaned}'")
    
    # Remove common LLM prefixes
    prefixes = [
        r'^the\s+(main\s+)?topic\s+(is|of\s+this\s+document\s+is)\s*:?\s*',
        r'^topic\s*:?\s*',
        r'^this\s+document\s+(is\s+about|discusses|covers)\s*:?\s*',
        r'^main\s+subject\s*:?\s*',
        r'^subject\s*:?\s*',
    ]
    
    for prefix in prefixes:
        before = cleaned
        cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
        if cleaned != before:
            logger.debug(f"[TOPIC CLEAN] After prefix removal: '{cleaned}'")
    
    # Remove quotes
    cleaned = cleaned.strip('"\'\'\'""`')
    
    # Remove trailing punctuation
    cleaned = cleaned.rstrip('.!?,;:')
    
    # Remove parentheses and brackets
    cleaned = re.sub(r'[\[\]\(\){}]', '', cleaned)
    
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # CRITICAL FIX: Remove malformed patterns like "Photosynthesis Concepts: -"
    # Match: optional words, then "Concepts:", then optional punctuation
    # Example: "Photosynthesis Concepts: -" -> "Photosynthesis"
    before_concept_fix = cleaned
    cleaned = re.sub(r'\s+[Cc]oncepts?\s*:.*$', '', cleaned)
    if cleaned != before_concept_fix:
        logger.debug(f"[TOPIC CLEAN] After concept removal: '{before_concept_fix}' -> '{cleaned}'")
    
    # Take only first 1-3 words (topic should be concise)
    words = cleaned.split()
    if len(words) > 3:
        cleaned = ' '.join(words[:3])
        logger.debug(f"[TOPIC CLEAN] Truncated to 3 words: '{cleaned}'")
    
    # Title case for consistency
    cleaned = cleaned.title() if cleaned else ""
    
    logger.debug(f"[TOPIC CLEAN] Final: '{cleaned}'")
    
    return cleaned


def topics_match(query_topic: str, document_topics: List[str], threshold: float = 0.6) -> bool:
    """
    Check if query topic matches any document topic using fuzzy matching.
    
    Args:
        query_topic: Normalized topic from user query
        document_topics: List of normalized topics from documents
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        True if a match is found, False otherwise
    """
    if not query_topic or not document_topics:
        return False
    
    query_norm = normalize_topic(query_topic)
    query_words = set(query_norm.split())
    
    for doc_topic in document_topics:
        doc_norm = normalize_topic(doc_topic)
        doc_words = set(doc_norm.split())
        
        # Exact match
        if query_norm == doc_norm:
            logger.info(f"[TOPIC MATCH] Exact: '{query_topic}' == '{doc_topic}'")
            return True
        
        # Substring match
        if query_norm in doc_norm or doc_norm in query_norm:
            logger.info(f"[TOPIC MATCH] Substring: '{query_topic}' <-> '{doc_topic}'")
            return True
        
        # Word overlap similarity (Jaccard similarity)
        if query_words and doc_words:
            intersection = query_words & doc_words
            union = query_words | doc_words
            similarity = len(intersection) / len(union)
            
            if similarity >= threshold:
                logger.info(f"[TOPIC MATCH] Fuzzy ({similarity:.2f}): '{query_topic}' ~ '{doc_topic}'")
                return True
    
    logger.warning(f"[TOPIC MISMATCH] Query '{query_topic}' not in {document_topics}")
    return False


def extract_unique_topics(metadatas: List[dict]) -> Set[str]:
    """
    Extract unique topic values from metadata list.
    
    Args:
        metadatas: List of metadata dictionaries
        
    Returns:
        Set of unique topics
    """
    topics = set()
    for metadata in metadatas:
        if metadata and 'document_topic' in metadata:
            topic = metadata['document_topic']
            if topic and isinstance(topic, str):
                topics.add(normalize_topic(topic))
    return topics


def extract_concepts_from_text(text: str, max_concepts: int = 5) -> List[str]:
    """
    Extract key concepts (nouns/entities) from text using simple heuristics.
    
    Args:
        text: Input text
        max_concepts: Maximum number of concepts to return
        
    Returns:
        List of concept strings
    """
    if not text:
        return []
    
    # Remove common question words
    question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'is', 'are', 'does', 'do', 'can', 'will', 'would', 'should']
    
    # Tokenize and clean
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove stop words and question words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'over'}
    
    concepts = []
    for word in words:
        if word not in stop_words and word not in question_words:
            concepts.append(word)
    
    # Return unique concepts, limited by max_concepts
    unique_concepts = []
    seen = set()
    for concept in concepts:
        if concept not in seen:
            unique_concepts.append(concept)
            seen.add(concept)
            if len(unique_concepts) >= max_concepts:
                break
    
    return unique_concepts


def normalize_concept(concept: str) -> str:
    """
    Normalize a concept for matching (handles CO2 vs carbon dioxide, etc.)
    
    Args:
        concept: Raw concept string
        
    Returns:
        Normalized concept
    """
    if not concept:
        return ""
    
    normalized = concept.lower().strip()
    
    # Handle common chemical/scientific abbreviations
    abbreviations = {
        'co2': 'carbon dioxide',
        'o2': 'oxygen',
        'h2o': 'water',
        'ai': 'artificial intelligence',
        'ml': 'machine learning',
        'rag': 'retrieval augmented generation',
        'llm': 'large language model',
        'gpu': 'graphics processing unit',
    }
    
    if normalized in abbreviations:
        return abbreviations[normalized]
    
    return normalized


def concepts_match(query_concepts: List[str], knowledge_concepts: List[str], threshold: float = 0.3) -> bool:
    """
    Check if any query concepts match knowledge base concepts.
    
    Args:
        query_concepts: Concepts from user query
        knowledge_concepts: Concepts from knowledge base
        threshold: Match threshold (fraction of query concepts that must match)
        
    Returns:
        True if sufficient concept overlap exists
    """
    if not query_concepts or not knowledge_concepts:
        return False
    
    # Normalize all concepts
    query_norm = [normalize_concept(c) for c in query_concepts]
    kb_norm = [normalize_concept(c) for c in knowledge_concepts]
    
    matches = 0
    for q_concept in query_norm:
        for kb_concept in kb_norm:
            # Exact match
            if q_concept == kb_concept:
                logger.info(f"[CONCEPT MATCH] Exact: '{q_concept}' == '{kb_concept}'")
                matches += 1
                break
            # Substring match
            elif q_concept in kb_concept or kb_concept in q_concept:
                logger.info(f"[CONCEPT MATCH] Substring: '{q_concept}' <-> '{kb_concept}'")
                matches += 1
                break
    
    match_ratio = matches / len(query_norm)
    if match_ratio >= threshold:
        logger.info(f"[CONCEPT MATCH] {matches}/{len(query_norm)} concepts matched ({match_ratio:.1%} >= {threshold:.1%})")
        return True
    
    logger.warning(f"[CONCEPT MISMATCH] Only {matches}/{len(query_norm)} concepts matched ({match_ratio:.1%} < {threshold:.1%})")
    return False
