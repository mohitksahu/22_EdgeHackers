"""
Qdrant query building utilities with Payload Filtering
"""
import logging
from typing import List, Dict, Any, Optional
from qdrant_client.http import models

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantQueryBuilder:
    """Builds Qdrant queries with proper filtering"""

    @staticmethod
    def build_topic_filter(document_topic: str) -> models.Filter:
        """Build filter for topic-concept gate matching"""
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="document_topic",
                    match=models.MatchValue(value=document_topic)
                )
            ]
        )

    @staticmethod
    def build_concept_filter(document_concepts: List[str]) -> models.Filter:
        """Build filter for concept matching"""
        return models.Filter(
            should=[
                models.FieldCondition(
                    key="document_concepts",
                    match=models.MatchAny(any=document_concepts)
                )
            ]
        )

    @staticmethod
    def build_modality_filter(modality: str) -> models.Filter:
        """Build filter for modality availability"""
        modality_field = f"has_{modality.lower()}"
        return models.Filter(
            must=[
                models.FieldCondition(
                    key=modality_field,
                    match=models.MatchValue(value=True)
                )
            ]
        )

    @staticmethod
    def build_source_filter(source_file: str) -> models.Filter:
        """Build filter for single source file matching"""
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="source_file",
                    match=models.MatchValue(value=source_file)
                )
            ]
        )

    @staticmethod
    def build_source_filter_multiple(source_files: List[str]) -> models.Filter:
        """Build filter for source file matching"""
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="source_file",
                    match=models.MatchAny(any=source_files)
                )
            ]
        )

    @staticmethod
    def combine_filters(*filters: models.Filter) -> models.Filter:
        """Combine multiple filters with AND logic"""
        combined_conditions = []
        for filter_obj in filters:
            if filter_obj.must:
                combined_conditions.extend(filter_obj.must)
            if filter_obj.should:
                combined_conditions.append(
                    models.FieldCondition(
                        key="combined_should",
                        match=models.MatchAny(any=filter_obj.should)
                    )
                )

        return models.Filter(must=combined_conditions)

    @staticmethod
    def get_vector_name_for_modality(modality: str) -> str:
        """Get the appropriate vector name for a modality"""
        modality_map = {
            "text": "text_vector_space",
            "image": "image_vector_space",
            "audio": "audio_vector"
        }
        return modality_map.get(modality.lower(), "text_vector_space")