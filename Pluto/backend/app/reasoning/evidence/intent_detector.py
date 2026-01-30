"""
Query intent detection for evidence validation
"""
import re
from typing import Literal

QueryIntent = Literal["identity", "locate", "general"]


def detect_query_intent(query: str) -> QueryIntent:
    """
    Detect the intent of a query without using LLMs
    
    Args:
        query: The user's query text
        
    Returns:
        'identity': Questions asking "who is X" or "what is X"
        'locate': Questions asking where something is mentioned
        'general': Everything else
    """
    query_lower = query.lower().strip()
    
    # Identity patterns: "who is X", "what is X", "who's X"
    identity_patterns = [
        r'^who\s+(is|was|are|were)\s+',
        r'^what\s+(is|was|are|were)\s+',
        r"^who'?s\s+",
        r"^what'?s\s+",
        r'^tell\s+me\s+(about|who)\s+',
        r'^describe\s+',
    ]
    
    for pattern in identity_patterns:
        if re.search(pattern, query_lower):
            return "identity"
    
    # Locate patterns: "where is X mentioned", "find X", "show me where"
    locate_patterns = [
        r'where\s+(is|are|was|were)\s+.+\s+mentioned',
        r'where\s+(does|did)\s+.+\s+(mention|say|state)',
        r'find\s+(the\s+)?(line|location|place|part)',
        r'show\s+me\s+where',
        r'get\s+me\s+the\s+line',
        r'in\s+which\s+(file|document|line)',
    ]
    
    for pattern in locate_patterns:
        if re.search(pattern, query_lower):
            return "locate"
    
    # Default to general
    return "general"


def has_descriptive_evidence(documents: list) -> bool:
    """
    Check if documents contain descriptive language (not just token matches)
    
    For identity queries, we need actual descriptive sentences like:
    - "is a developer"
    - "works as an engineer"
    - "known for building X"
    
    NOT just:
    - File trees with names
    - Code snippets with variable names
    - Token matches without context
    
    Args:
        documents: List of retrieved document dicts
        
    Returns:
        True if documents contain descriptive evidence
    """
    if not documents:
        return False
    
    # Descriptive indicators - phrases that suggest actual descriptions
    descriptive_indicators = [
        r'\b(is|was|are|were)\s+a\s+',
        r'\b(is|was|are|were)\s+an\s+',
        r'\bworks?\s+(as|at|for)\s+',
        r'\bknown\s+for\s+',
        r'\bspecializes?\s+in\s+',
        r'\bexpert\s+in\s+',
        r'\b(developer|engineer|designer|manager|scientist|researcher)\b',
        r'\b(he|she|they)\s+(is|was|are|were)\s+',
        r'\bresponsible\s+for\s+',
        r'\brole\s+(is|was)\s+',
        r'\bposition\s+(is|was)\s+',
        r'\btitle\s+(is|was)\s+',
        r'\bbackground\s+in\s+',
        r'\bexperience\s+(in|with)\s+',
    ]
    
    # Anti-patterns - things that suggest non-descriptive content
    anti_patterns = [
        r'^[\s\│\├\└\-]+',  # File tree characters
        r'^\s*[/\\]',  # File paths
        r'^\s*(def|class|function|const|let|var)\s+',  # Code definitions
        r'^\s*import\s+',  # Import statements
        r'^\s*#include\s+',  # C/C++ includes
        r'^\s*package\s+',  # Package declarations
    ]
    
    descriptive_count = 0
    
    for doc in documents:
        content = doc.get('content', '').lower()
        
        if not content or len(content.strip()) < 20:
            continue
        
        # Check for anti-patterns first
        is_code_or_tree = any(re.search(pattern, content[:100]) for pattern in anti_patterns)
        if is_code_or_tree:
            continue
        
        # Check for descriptive indicators
        has_descriptor = any(re.search(pattern, content) for pattern in descriptive_indicators)
        if has_descriptor:
            descriptive_count += 1
    
    # Require at least one document with descriptive content
    return descriptive_count > 0
