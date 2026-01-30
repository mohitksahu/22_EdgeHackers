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
        """
        content1 = doc1.get("content", "")[:1500]
        content2 = doc2.get("content", "")[:1500]

        metadata1 = doc1.get("metadata", {})
        metadata2 = doc2.get("metadata", {})

        source1_path = metadata1.get("source_file") or metadata1.get("file_path", "Unknown")
        source2_path = metadata2.get("source_file") or metadata2.get("file_path", "Unknown")

        def extract_name(path):
            if isinstance(path, str):
                path = path.replace("\\", "/")
                return path.split("/")[-1]
            return "Unknown"

        source1_name = extract_name(source1_path)
        source2_name = extract_name(source2_path)

        system_prompt = """You are a conflict detection expert. Your task is to identify contradictory information between two evidence sources.

Respond ONLY in this exact format:
Conflict: [yes/no]
Description: [brief summary of the contradiction, or 'No conflict']

A conflict exists when the sources provide incompatible or contradictory answers to the same question.
Minor differences in detail are NOT conflicts unless they fundamentally contradict each other.
"""

        user_prompt = f"""Question: {query}

Source A ({source1_name}):
{content1}

Source B ({source2_name}):
{content2}

Do these sources provide contradictory information relevant to the question?
"""

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            response = self.reasoner.generate(
                prompt=full_prompt,
                max_tokens=150,
                temperature=0.1,
                stop_sequences=["Question:", "Source A:", "Source B:"]
            )

            conflict_line = ""
            description_line = ""

            for line in response.split("\n"):
                if line.lower().startswith("conflict:"):
                    conflict_line = line.lower()
                elif line.startswith("Description:"):
                    description_line = line.split("Description:", 1)[1].strip()

            has_conflict = "yes" in conflict_line

            if has_conflict and description_line and "no conflict" not in description_line.lower():
                conflict_desc = f"Conflict between {source1_name} and {source2_name}: {description_line}"
                logger.warning(conflict_desc)
                return conflict_desc

            return ""

        except Exception as e:
            logger.error(f"Error checking conflict: {e}")
            return ""

    async def run(self, state: GraphState) -> GraphState:
        """
        Graph-compatible entrypoint.
        Detect conflicts across all pairs of retrieved documents.
        """
        query = state["query"]
        documents = state.get("retrieved_documents", [])

        logger.info(f"Checking for conflicts among {len(documents)} documents...")

        if len(documents) < 2:
            state["conflicts"] = []
            state["is_conflicting"] = False
            return state

        docs_to_check = documents[:5]
        conflicts: List[str] = []

        for (doc1, doc2) in combinations(docs_to_check, 2):
            meta1 = doc1.get("metadata", {})
            meta2 = doc2.get("metadata", {})

            src1 = meta1.get("source_file") or meta1.get("file_path")
            src2 = meta2.get("source_file") or meta2.get("file_path")

            if src1 and src2 and src1 == src2:
                continue

            conflict = self.check_conflict(doc1, doc2, query)
            if conflict:
                conflicts.append(conflict)

        state["conflicts"] = conflicts
        state["is_conflicting"] = len(conflicts) > 0

        if state["is_conflicting"]:
            logger.warning(f"Detected {len(conflicts)} conflicts")
        else:
            logger.info("No conflicts detected")

        return state


# Singleton instance
conflict_detector = ConflictDetector()
