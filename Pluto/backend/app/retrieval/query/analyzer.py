"""
Query Analyzer - Intent classification and modality detection for multimodal RAG
"""
import logging
from enum import Enum
from typing import List

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query intent types for modality-aware retrieval"""
    VISUAL_ATTRIBUTE = "visual_attribute"  # Color, shape, size, appearance
    VISUAL_DESCRIPTION = "visual_description"  # What's in the image
    VISUAL_IDENTITY = "visual_identity"  # Who/what is this object
    AUDIO_CONTENT = "audio_content"  # What was said in audio
    TEXT_SEARCH = "text_search"  # General text search (default)


class QueryAnalyzer:
    """Analyzes queries to determine intent and required modalities"""
    
    # Keywords for intent detection (priority order matters)
    VISUAL_ATTRIBUTE_KEYWORDS = [
        'color', 'colour', 'shape', 'size', 'appearance', 'look', 'looks',
        'wear', 'wearing', 'clothing', 'shirt', 'dress', 'outfit', 'pants',
        'shoes', 'hat', 'jacket', 'clothes',
        # Color words
        'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown',
        'black', 'white', 'gray', 'grey', 'violet', 'indigo', 'cyan', 'magenta',
        # Shape/size words
        'round', 'square', 'rectangular', 'circular', 'oval', 'triangular',
        'big', 'small', 'large', 'tiny', 'huge', 'tall', 'short', 'wide', 'narrow'
    ]
    
    VISUAL_DESCRIPTION_KEYWORDS = [
        'image', 'picture', 'photo', 'see', 'show', 'visible', 'shown',
        'in the image', 'in the picture', 'in the photo',
        'what is in', 'what\'s in', 'what do you see', 'describe the'
    ]
    
    AUDIO_CONTENT_KEYWORDS = [
        'said', 'mentioned', 'audio', 'recording', 'voice', 'transcript',
        'spoken', 'discussed', 'talked', 'conversation', 'interview',
        'what did', 'what was said', 'listen', 'hear', 'heard'
    ]
    
    VISUAL_IDENTITY_KEYWORDS = [
        'who is', 'what is this', 'who\'s this', 'identify', 'person in',
        'who are', 'name of', 'which person'
    ]
    
    def classify_intent(self, query: str) -> QueryIntent:
        """
        Classify query intent based on keyword matching.
        Priority order: visual_attribute > visual_description > audio_content > visual_identity > text_search
        
        Args:
            query: User query string
            
        Returns:
            QueryIntent enum value
        """
        query_lower = query.lower()
        
        # Priority 1: Visual attributes (most specific)
        if any(keyword in query_lower for keyword in self.VISUAL_ATTRIBUTE_KEYWORDS):
            logger.info(f"[ANALYZER] Classified as VISUAL_ATTRIBUTE: '{query}'")
            return QueryIntent.VISUAL_ATTRIBUTE
        
        # Priority 2: Visual description
        if any(keyword in query_lower for keyword in self.VISUAL_DESCRIPTION_KEYWORDS):
            logger.info(f"[ANALYZER] Classified as VISUAL_DESCRIPTION: '{query}'")
            return QueryIntent.VISUAL_DESCRIPTION
        
        # Priority 3: Audio content
        if any(keyword in query_lower for keyword in self.AUDIO_CONTENT_KEYWORDS):
            logger.info(f"[ANALYZER] Classified as AUDIO_CONTENT: '{query}'")
            return QueryIntent.AUDIO_CONTENT
        
        # Priority 4: Visual identity
        if any(keyword in query_lower for keyword in self.VISUAL_IDENTITY_KEYWORDS):
            logger.info(f"[ANALYZER] Classified as VISUAL_IDENTITY: '{query}'")
            return QueryIntent.VISUAL_IDENTITY
        
        # Default: Text search
        logger.info(f"[ANALYZER] Classified as TEXT_SEARCH (default): '{query}'")
        return QueryIntent.TEXT_SEARCH
    
    def get_required_modalities(self, intent: QueryIntent) -> List[str]:
        """
        Map query intent to required modalities for retrieval filtering.
        
        Args:
            intent: QueryIntent enum value
            
        Returns:
            List of required modality strings
        """
        modality_map = {
            QueryIntent.VISUAL_ATTRIBUTE: ["image"],
            QueryIntent.VISUAL_DESCRIPTION: ["image"],
            QueryIntent.VISUAL_IDENTITY: ["image", "text"],
            QueryIntent.AUDIO_CONTENT: ["audio", "text"],
            QueryIntent.TEXT_SEARCH: ["text"]
        }
        
        modalities = modality_map.get(intent, ["text"])
        logger.debug(f"[ANALYZER] Intent {intent.value} requires modalities: {modalities}")
        return modalities
    
    def is_visual_intent(self, intent: QueryIntent) -> bool:
        """Check if the intent requires visual evidence"""
        return intent in [
            QueryIntent.VISUAL_ATTRIBUTE,
            QueryIntent.VISUAL_DESCRIPTION,
            QueryIntent.VISUAL_IDENTITY
        ]
