import logging
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


class RefusalNode:
    """
    Explains WHY the system refuses to answer.
    """

    async def run(self, state: GraphState) -> GraphState:
        reason = self._determine_reason(state)

        state["final_response"] = (
            "I’m unable to answer this question.\n\n"
            f"Reason: {reason}"
        )
        state["status"] = "refused"
        return state

    def _determine_reason(self, state: GraphState) -> str:
        if state.get("is_out_of_scope"):
            return (
                "The question does not match the topics or concepts "
                "present in the uploaded documents."
            )

        if not state.get("retrieved_documents"):
            return (
                "No relevant information was found in the uploaded documents."
            )

        if not state.get("is_sufficient"):
            return (
                "The available evidence was too weak or insufficient "
                "to support a reliable answer."
            )

        return "The system could not verify the answer with high confidence."
