"""
Conflict Detector Node - GPU Accelerated
Cross-references sources to identify contradictory information across modalities.
"""
import logging
from typing import Dict, List
from itertools import combinations
from app.graph.state import GraphState
from app.reasoning.llm.llama_reasoner import LlamaReasoner

logger = logging.getLogger(__name__)

class ConflictDetector:
    """Detects contradictions between retrieved sources using LLM"""
    
    def __init__(self):
        self.reasoner = LlamaReasoner()
        
    def check_conflict(self, doc1: Dict, doc2: Dict, query: str) -> str:
        """
        Compare two documents to detect contradictions.
        
        Args:
            doc1: First document dict
            doc2: Second document dict
            query: User's question for context
            
        Returns:
            Conflict description if found, empty string otherwise
        """
        content1 = doc1.get('content', '')[:1500]
        content2 = doc2.get('content', '')[:1500]
        
        # Get source identifiers from metadata
        metadata1 = doc1.get('metadata', {})
        metadata2 = doc2.get('metadata', {})
        
        # Extract filename from path (handle Windows and Unix paths)
        source1_path = metadata1.get('source_file') or metadata1.get('file_path', 'Unknown')
        source2_path = metadata2.get('source_file') or metadata2.get('file_path', 'Unknown')
        
        # Normalize and extract just the filename
        if isinstance(source1_path, str):
            source1_path = source1_path.replace('\\', '/').replace('\\', '/')
            source1_name = source1_path.split('/')[-1] if '/' in source1_path else source1_path
        else:
            source1_name = 'Unknown'
            
        if isinstance(source2_path, str):
            source2_path = source2_path.replace('\\', '/').replace('\\', '/')
            source2_name = source2_path.split('/')[-1] if '/' in source2_path else source2_path
        else:
            source2_name = 'Unknown'
        
        system_prompt = """You are a conflict detection expert. Your task is to identify contradictory information between two evidence sources.

Respond ONLY in this exact format:
Conflict: [yes/no]
Description: [brief summary of the contradiction, or 'No conflict']

A conflict exists when the sources provide incompatible or contradictory answers to the same question.
Minor differences in detail are NOT conflicts unless they fundamentally contradict each other."""
        
        user_prompt = f"""Question: {query}

Source A ({source1} - {source1_name}):
{content1}

Source B ({source2} - {source2_name}):
{content2}

Do these sources provide contradictory information relevant to the question?"""
        
        # Combine into single prompt for generate()
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            response = self.reasoner.generate(
                prompt=full_prompt,
                max_tokens=150,
                temperature=0.1,
                stop_sequences=["Question:", "Source A:", "Source B:"]
            )
            
            # Parse response
            conflict_line = ""
            description_line = ""
            for line in response.split('\n'):
                if line.startswith('Conflict:'):
                    conflict_line = line.lower()
                elif line.startswith('Description:'):
                    description_line = line.split('Description:', 1)[1].strip()
            
            has_conflict = 'yes' in conflict_line
            
            if has_conflict and description_line and 'no conflict' not in description_line.lower():
                # Format conflict description for frontend yellow warning box
                conflict_desc = f"Conflict between {source1_name} and {source2_name}: {description_line}"
                logger.info(f"Conflict detected: {conflict_desc}")
                return conflict_desc
            else:
                logger.debug(f"No conflict between {source1_name} and {source2_name}")
                return ""
                
        except Exception as e:
            logger.error(f"Error checking conflict: {e}")
            return ""
    
    async def run(self, state: GraphState) -> GraphState:
        """
        Graph-compatible entrypoint.
        Detect conflicts across all pairs of retrieved documents.
        
        Sets:
            - conflicts: List of conflict descriptions
            - is_conflicting: Boolean flag (True if any conflicts found)
        """
        query = state["query"]
        documents = state.get("retrieved_documents", [])
        
        logger.info(f"Checking for conflicts among {len(documents)} documents...")
        
        conflicts = []
        
        # Only check conflicts if we have 2+ documents
        if len(documents) < 2:
            logger.info("Less than 2 documents, skipping conflict detection")
            state["conflicts"] = []
            state["is_conflicting"] = False
            return state
        
        # Check all pairs of documents
        # Limit to top 5 documents to avoid O(n^2) explosion
        docs_to_check = documents[:5]
        pairs = list(combinations(enumerate(docs_to_check), 2))
        
        logger.info(f"Checking {len(pairs)} document pairs for conflicts...")
        
        for (idx1, doc1), (idx2, doc2) in pairs:
            # Skip pairs from the same source file
            metadata1 = doc1.get('metadata', {})
            metadata2 = doc2.get('metadata', {})
            
            source1_path = metadata1.get('source_file') or metadata1.get('file_path', '')
            source2_path = metadata2.get('source_file') or metadata2.get('file_path', '')
            
            if source1_path and source2_path and source1_path == source2_path:
                continue  # Same source file, skip
            
            conflict = self.check_conflict(doc1, doc2, query)
            if conflict:
                conflicts.append(conflict)
        
        # Update state
        state["conflicts"] = conflicts
        state["is_conflicting"] = len(conflicts) > 0
        
        if state["is_conflicting"]:
            logger.warning(f"Detected {len(conflicts)} conflicts in evidence")
            for conflict in conflicts:
                logger.warning(f"  - {conflict}")
        else:
            logger.info("No conflicts detected in evidence")
        
        return state


# Singleton instance
conflict_detector = ConflictDetector()
