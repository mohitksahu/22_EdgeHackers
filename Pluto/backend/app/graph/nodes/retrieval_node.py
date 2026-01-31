from app.retrieval.orchestrator import RetrievalOrchestrator
from app.retrieval.strategies.multimodal_strategy import multimodal_retrieve
from app.retrieval.query.multi_query_generator import generate_multi_queries
from app.reasoning.llm.llama_reasoner import LlamaReasoner
from app.graph.state import GraphState
from app.utils.logging_utils import safe_text
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class RetrievalNode:
    """Node B: The Librarian (Retrieval - Modality-Agnostic)"""
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.executor = ThreadPoolExecutor(max_workers=4)  # Parallel queries
        self.llama_client = LlamaReasoner()  # Initialize LlamaReasoner for query generation
    
    async def run(self, state: GraphState) -> GraphState:
        """Parallel multi-query retrieval"""
        query = state["query"]
        session_id = state.get("session_id", "default")
        top_k = state.get("top_k", 10)
        
        # Generate multiple queries using the function
        queries = await generate_multi_queries(query, self.llama_client)
        
        # Execute queries in parallel
        logger.info(f"Executing {len(queries)} queries in parallel")
        
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                self.executor,
                self.orchestrator.vector_store.query,
                q,
                session_id,
                top_k
            )
            for q in queries
        ]
        
        # Wait for all queries to complete
        results_list = await asyncio.gather(*tasks)
        
        # Merge and deduplicate
        all_results = []
        seen_ids = set()
        
        for results in results_list:
            documents = results.get('documents', [])
            ids = results.get('ids', [])
            metadatas = results.get('metadatas', [])
            distances = results.get('distances', [])
            
            for i in range(len(documents)):
                doc_id = ids[i] if i < len(ids) else f'doc_{i}'
                
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    all_results.append({
                        'id': doc_id,
                        'content': documents[i],
                        'metadata': metadatas[i] if i < len(metadatas) else {},
                        'score': 1.0 - distances[i] if i < len(distances) else 0.0,
                        'modality': metadatas[i].get('modality', 'text') if i < len(metadatas) else 'text'
                    })
        
        # Sort by score and limit
        all_results.sort(key=lambda x: x['score'], reverse=True)
        state["retrieved_documents"] = all_results[:top_k]
        
        logger.info(f"Retrieved {len(state['retrieved_documents'])} unique documents")
        return state
