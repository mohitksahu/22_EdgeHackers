"""
Topic catalog logging for persistence and observability
"""
import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)


def log_topic_catalog(topics: List[str], log_dir: Optional[Path] = None) -> bool:
    """
    Log the current topic catalog to a JSON file for persistence.
    
    Args:
        topics: List of available topics in the knowledge base
        log_dir: Directory to save the catalog (defaults to data/logs/retrieval/)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if log_dir is None:
            log_dir = settings.logs_dir / "retrieval"
        
        # Ensure directory exists
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare catalog data
        catalog = {
            "timestamp": datetime.now().isoformat(),
            "topic_count": len(topics),
            "topics": sorted(topics)
        }
        
        # Write to file
        catalog_path = log_dir / "current_topic_catalog.json"
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Topic catalog logged to {catalog_path}")
        logger.info(f"Current knowledge base covers: {', '.join(topics)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log topic catalog: {e}")
        return False


def load_topic_catalog(log_dir: Optional[Path] = None) -> List[str]:
    """
    Load the persisted topic catalog from JSON file.
    
    Args:
        log_dir: Directory containing the catalog
        
    Returns:
        List of topics, empty list if file not found
    """
    try:
        if log_dir is None:
            log_dir = settings.logs_dir / "retrieval"
        
        catalog_path = log_dir / "current_topic_catalog.json"
        
        if not catalog_path.exists():
            logger.warning(f"Topic catalog not found at {catalog_path}")
            return []
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        
        topics = catalog.get('topics', [])
        logger.info(f"Loaded {len(topics)} topics from catalog")
        return topics
        
    except Exception as e:
        logger.error(f"Failed to load topic catalog: {e}")
        return []
