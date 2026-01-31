"""
Base Processor - Abstract class for all processors
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.core.logging_config import get_safe_logger

logger = get_safe_logger(__name__)


class BaseProcessor(ABC):
    """Abstract base class for all document processors"""
    
    def __init__(self):
        self.supported_extensions: List[str] = []
    
    @abstractmethod
    def process(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a file and return chunks
        
        Args:
            file_path: Path to the file
            metadata: Optional metadata dict
            
        Returns:
            List of chunk dictionaries with 'content', 'modality', etc.
        """
        pass
    
    def can_process(self, file_path: str) -> bool:
        """Check if this processor can handle the file"""
        ext = Path(file_path).suffix.lower()
        return ext in self.supported_extensions