"""
Qdrant Vector Store - Fixed collection info method
"""
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.core.logging_config import get_safe_logger

logger = get_safe_logger(__name__)


class VectorStore:
    """
    Qdrant Vector Store with multi-vector support
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if VectorStore._initialized:
            return
        
        self.collection_name = settings.collection_name
        self.qdrant_client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            prefer_grpc=settings.qdrant_prefer_grpc
        )
        
        # Vector configurations for multimodal
        self.vector_config = {
            "text_embedding": qmodels.VectorParams(
                size=settings.embedding_dimension,  # 512 for CLIP
                distance=qmodels.Distance.COSINE
            ),
            "image_embedding": qmodels.VectorParams(
                size=settings.embedding_dimension,
                distance=qmodels.Distance.COSINE
            ),
            "audio_embedding": qmodels.VectorParams(
                size=settings.embedding_dimension,
                distance=qmodels.Distance.COSINE
            ),
        }
        
        # Ensure collection exists
        self._ensure_collection()
        
        VectorStore._initialized = True
        logger.info(f"[OK] VectorStore initialized: {self.collection_name}")
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"[INFO] Creating collection: {self.collection_name}")
                self._create_collection()
            else:
                logger.info(f"[OK] Collection exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"[FAIL] Error with collection: {e}")
            raise
    
    def _create_collection(self):
        """Create the multimodal collection"""
        try:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=self.vector_config,
                optimizers_config=qmodels.OptimizersConfigDiff(
                    indexing_threshold=10000,
                ),
            )
            
            # Create indexes
            self._create_indexes()
            logger.info(f"[OK] Collection created: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to create collection: {e}")
            raise
    
    def _create_indexes(self):
        """Create payload indexes for filtering"""
        index_fields = [
            ("session_id", qmodels.PayloadSchemaType.KEYWORD),
            ("modality", qmodels.PayloadSchemaType.KEYWORD),
            ("document_topic", qmodels.PayloadSchemaType.KEYWORD),
            ("file_name", qmodels.PayloadSchemaType.KEYWORD),
        ]
        
        for field_name, field_type in index_fields:
            try:
                self.qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                )
            except Exception:
                pass  # Index may already exist
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add documents with embeddings to Qdrant"""
        if not documents:
            return {"status": "success", "indexed": 0}
        
        try:
            points = []
            
            for doc in documents:
                point_id = doc.get('id') or str(uuid.uuid4())
                
                # Build vectors dict
                vectors = {}
                if doc.get('text_embedding'):
                    vectors['text_embedding'] = doc['text_embedding']
                if doc.get('image_embedding'):
                    vectors['image_embedding'] = doc['image_embedding']
                if doc.get('audio_embedding'):
                    vectors['audio_embedding'] = doc['audio_embedding']
                
                if not vectors:
                    continue
                
                point = qmodels.PointStruct(
                    id=point_id,
                    vector=vectors,
                    payload=doc.get('payload', {})
                )
                points.append(point)
            
            if not points:
                return {"status": "warning", "indexed": 0, "message": "No valid points"}
            
            # Upsert in batches
            batch_size = 100
            total_indexed = 0
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True
                )
                total_indexed += len(batch)
            
            logger.info(f"[OK] Indexed {total_indexed} documents")
            return {"status": "success", "indexed": total_indexed}
            
        except UnexpectedResponse as e:
            if "doesn't exist" in str(e):
                logger.info("[INFO] Collection missing, recreating...")
                self._create_collection()
                return self.add_documents(documents)
            logger.error(f"[FAIL] Upsert failed: {e}")
            raise
        except Exception as e:
            logger.error(f"[FAIL] Add documents failed: {e}")
            raise
    
    def query(
        self,
        query_embedding: List[float],
        session_id: Optional[str] = None,
        vector_name: str = "text_embedding",
        n_results: int = 10,
        score_threshold: float = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query a single vector space in the vector store"""
        try:
            # Build filter
            must_conditions = []
            
            if session_id:
                must_conditions.append(
                    qmodels.FieldCondition(
                        key="session_id",
                        match=qmodels.MatchValue(value=session_id)
                    )
                )
            
            if filters:
                for key, value in filters.items():
                    must_conditions.append(
                        qmodels.FieldCondition(
                            key=key,
                            match=qmodels.MatchValue(value=value)
                        )
                    )
            
            query_filter = qmodels.Filter(must=must_conditions) if must_conditions else None
            
            # Use query_points for qdrant-client >= 1.7.0
            results = self.qdrant_client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                using=vector_name,
                query_filter=query_filter,
                limit=n_results,
                score_threshold=score_threshold or settings.similarity_threshold,
                with_payload=True,
            ).points
            
            # Format results
            ids = []
            documents = []
            metadatas = []
            scores = []
            
            for result in results:
                ids.append(str(result.id))
                payload = result.payload or {}
                documents.append(payload.get('content', ''))
                metadatas.append(payload)
                scores.append(result.score)
            
            return {
                "status": "success",
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "scores": scores,
                "distances": [1.0 - s for s in scores],
                "vector_space": vector_name
            }
            
        except Exception as e:
            logger.error(f"[FAIL] Query failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def query_multimodal(
        self,
        query_embedding: List[float],
        session_id: Optional[str] = None,
        vector_spaces: List[str] = None,
        n_results: int = 10,
        score_threshold: float = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query across multiple vector spaces and merge results.
        
        This searches text_embedding, image_embedding, and audio_embedding
        spaces and returns deduplicated, ranked results.
        
        Args:
            query_embedding: The query vector (from CLIP text encoder)
            session_id: Filter by session
            vector_spaces: Which spaces to search. Defaults to all.
            n_results: Total number of results to return
            score_threshold: Minimum similarity score
            filters: Additional payload filters
            
        Returns:
            Merged and deduplicated results from all vector spaces
        """
        # Default to all vector spaces
        if vector_spaces is None:
            vector_spaces = ["text_embedding", "image_embedding", "audio_embedding"]
        
        all_results = []
        seen_ids = set()
        
        logger.info(f"[MULTIMODAL SEARCH] Searching {len(vector_spaces)} vector spaces")
        
        for vector_space in vector_spaces:
            try:
                results = self.query(
                    query_embedding=query_embedding,
                    session_id=session_id,
                    vector_name=vector_space,
                    n_results=n_results,  # Get full count from each
                    score_threshold=score_threshold,
                    filters=filters
                )
                
                if results.get('status') != 'success':
                    continue
                
                # Add results with vector space info
                for idx in range(len(results.get('ids', []))):
                    doc_id = results['ids'][idx]
                    
                    # Deduplicate by ID (same document may match in multiple spaces)
                    if doc_id in seen_ids:
                        # Update score if this space gives higher score
                        for r in all_results:
                            if r['id'] == doc_id:
                                new_score = results['scores'][idx]
                                if new_score > r['score']:
                                    r['score'] = new_score
                                    r['matched_vector_space'] = vector_space
                                # Track all spaces this document matched
                                r['matched_spaces'].append(vector_space)
                                break
                        continue
                    
                    seen_ids.add(doc_id)
                    
                    all_results.append({
                        'id': doc_id,
                        'content': results['documents'][idx],
                        'metadata': results['metadatas'][idx],
                        'score': results['scores'][idx],
                        'matched_vector_space': vector_space,
                        'matched_spaces': [vector_space]
                    })
                    
            except Exception as e:
                logger.warning(f"[WARN] Query failed for {vector_space}: {e}")
                continue
        
        if not all_results:
            return {
                "status": "success",
                "ids": [],
                "documents": [],
                "metadatas": [],
                "scores": [],
                "distances": [],
                "searched_spaces": vector_spaces,
                "total_results": 0
            }
        
        # Sort by score (highest first)
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Limit to n_results
        all_results = all_results[:n_results]
        
        # Format output
        ids = [r['id'] for r in all_results]
        documents = [r['content'] for r in all_results]
        metadatas = []
        scores = [r['score'] for r in all_results]
        
        for r in all_results:
            meta = r['metadata'].copy()
            meta['matched_vector_space'] = r['matched_vector_space']
            meta['matched_spaces'] = r['matched_spaces']
            metadatas.append(meta)
        
        logger.info(f"[MULTIMODAL SEARCH] Found {len(ids)} unique results across {vector_spaces}")
        
        return {
            "status": "success",
            "ids": ids,
            "documents": documents,
            "metadatas": metadatas,
            "scores": scores,
            "distances": [1.0 - s for s in scores],
            "searched_spaces": vector_spaces,
            "total_results": len(ids)
        }
    
    def delete_by_session(self, session_id: str) -> Dict[str, Any]:
        """Delete all documents for a session"""
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="session_id",
                                match=qmodels.MatchValue(value=session_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"[OK] Deleted documents for session: {session_id}")
            return {"status": "success"}
        except Exception as e:
            logger.error(f"[FAIL] Delete failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            info = self.qdrant_client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "indexed_vectors_count": getattr(info, 'indexed_vectors_count', 'N/A'),
                "status": str(info.status),
            }
        except Exception as e:
            logger.error(f"[FAIL] Failed to get collection info: {e}")
            return {"error": str(e)}
    
    def collection_exists(self) -> bool:
        """Check if collection exists"""
        try:
            collections = self.qdrant_client.get_collections()
            return self.collection_name in [c.name for c in collections.collections]
        except Exception:
            return False