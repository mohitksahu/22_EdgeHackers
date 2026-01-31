"""
Multi-Agent LangGraph Workflow
Orchestrates specialized agents for RAG pipeline
"""
import logging
from typing import Dict, Any, TypedDict, Annotated, Sequence, Literal
import operator
from langgraph.graph import StateGraph, END

from app.graph.agents.supervisor import SupervisorAgent, AgentTask
from app.graph.agents.retrieval_agent import RetrievalAgent
from app.graph.agents.reasoning_agent import ReasoningAgent
from app.graph.agents.validation_agent import ValidationAgent
from app.graph.agents.response_agent import ResponseAgent
from app.config import settings

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State shared across all agents"""
    # Input
    query: str
    session_id: str
    top_k: int
    
    # Retrieval results
    retrieved_documents: list
    evidence: list
    query_variations: list
    retrieval_methods: list
    retrieval_attempted: bool
    
    # Validation results
    validation_passed: bool
    evidence_score: float
    conflicts: list
    validation_reason: str
    
    # Reasoning results
    reasoning_result: dict
    synthesized_answer: str
    reasoning_complete: bool
    reasoning_confidence: float
    
    # Final output
    final_response: dict
    workflow_complete: bool
    
    # Control
    workflow_plan: Any
    current_agent: str
    agent_history: Annotated[Sequence[str], operator.add]
    error: str


def create_multi_agent_graph():
    """
    Create the multi-agent workflow graph
    
    Flow:
    supervisor -> retrieval -> validation -> reasoning -> response
                    ^              |              |
                    |______________|______________|
                    (retry if needed)
    """
    
    # Initialize agents
    supervisor = SupervisorAgent()
    retrieval_agent = RetrievalAgent()
    validation_agent = ValidationAgent()
    reasoning_agent = ReasoningAgent()
    response_agent = ResponseAgent()
    
    # Define node functions
    async def supervisor_node(state: AgentState) -> AgentState:
        """Supervisor decides next action"""
        result = await supervisor.execute(state)
        state['current_agent'] = result.next_agent or 'end'
        state['agent_history'] = [f"supervisor->{result.next_agent}"]
        return state
    
    async def retrieval_node(state: AgentState) -> AgentState:
        """Execute retrieval"""
        result = await retrieval_agent.execute(state)
        state.update(result.data)
        state['agent_history'] = ['retrieval']
        return state
    
    async def validation_node(state: AgentState) -> AgentState:
        """Execute validation"""
        result = await validation_agent.execute(state)
        state.update(result.data)
        state['agent_history'] = ['validation']
        return state
    
    async def reasoning_node(state: AgentState) -> AgentState:
        """Execute reasoning"""
        result = await reasoning_agent.execute(state)
        state.update(result.data)
        state['agent_history'] = ['reasoning']
        return state
    
    async def response_node(state: AgentState) -> AgentState:
        """Generate final response"""
        result = await response_agent.execute(state)
        state.update(result.data)
        state['agent_history'] = ['response']
        return state
    
    # Routing functions
    def route_from_supervisor(state: AgentState) -> Literal["retrieval", "validation", "reasoning", "response", "end"]:
        """Route based on supervisor decision"""
        current = state.get('current_agent', 'retrieval')
        if current in ['retrieval', 'validation', 'reasoning', 'response']:
            return current
        return 'end'
    
    def route_from_retrieval(state: AgentState) -> Literal["validation", "response"]:
        """Route after retrieval"""
        if state.get('retrieved_documents'):
            return 'validation'
        return 'response'  # No documents, go to refusal
    
    def route_from_validation(state: AgentState) -> Literal["reasoning", "response"]:
        """Route after validation"""
        if state.get('validation_passed', False):
            return 'reasoning'
        # Low confidence but has evidence, still try reasoning
        if state.get('evidence_score', 0) >= settings.refusal_threshold:
            return 'reasoning'
        return 'response'  # Refuse
    
    def route_from_reasoning(state: AgentState) -> Literal["response"]:
        """Route after reasoning"""
        return 'response'
    
    # Build graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("response", response_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add edges
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "retrieval": "retrieval",
            "validation": "validation",
            "reasoning": "reasoning",
            "response": "response",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "retrieval",
        route_from_retrieval,
        {
            "validation": "validation",
            "response": "response"
        }
    )
    
    workflow.add_conditional_edges(
        "validation",
        route_from_validation,
        {
            "reasoning": "reasoning",
            "response": "response"
        }
    )
    
    workflow.add_edge("reasoning", "response")
    workflow.add_edge("response", END)
    
    # Compile
    return workflow.compile()


# Create singleton graph instance
_multi_agent_graph = None


def get_multi_agent_graph():
    """Get or create the multi-agent graph"""
    global _multi_agent_graph
    if _multi_agent_graph is None:
        _multi_agent_graph = create_multi_agent_graph()
    return _multi_agent_graph


async def run_multi_agent_query(
    query: str,
    session_id: str = "default",
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Execute a query through the multi-agent workflow
    
    Args:
        query: User query
        session_id: Session identifier
        top_k: Number of documents to retrieve
        
    Returns:
        Final response with metadata
    """
    graph = get_multi_agent_graph()
    
    initial_state: AgentState = {
        "query": query,
        "session_id": session_id,
        "top_k": top_k,
        "retrieved_documents": [],
        "evidence": [],
        "query_variations": [],
        "retrieval_methods": [],
        "retrieval_attempted": False,
        "validation_passed": False,
        "evidence_score": 0.0,
        "conflicts": [],
        "validation_reason": "",
        "reasoning_result": {},
        "synthesized_answer": "",
        "reasoning_complete": False,
        "reasoning_confidence": 0.0,
        "final_response": {},
        "workflow_complete": False,
        "workflow_plan": None,
        "current_agent": "supervisor",
        "agent_history": [],
        "error": ""
    }
    
    try:
        final_state = await graph.ainvoke(initial_state)
        
        return {
            "success": True,
            "response": final_state.get('final_response', {}),
            "evidence_score": final_state.get('evidence_score', 0.0),
            "agent_history": final_state.get('agent_history', []),
            "documents_retrieved": len(final_state.get('retrieved_documents', [])),
            "retrieval_methods": final_state.get('retrieval_methods', [])
        }
        
    except Exception as e:
        logger.error(f"Multi-agent workflow failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": {
                "refusal": True,
                "answer": f"Workflow error: {str(e)}",
                "confidence": 0.0
            }
        }