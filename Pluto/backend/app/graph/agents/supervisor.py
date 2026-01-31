"""
Supervisor Agent - Orchestrates multi-agent workflow
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.graph.agents.base_agent import BaseAgent, AgentResponse
from app.config import settings

logger = logging.getLogger(__name__)


class AgentTask(Enum):
    """Available agent tasks"""
    RETRIEVE = "retrieval"
    REASON = "reasoning"
    VALIDATE = "validation"
    RESPOND = "response"
    COMPLETE = "complete"
    REFUSE = "refuse"


@dataclass
class WorkflowPlan:
    """Plan for executing workflow"""
    tasks: List[AgentTask]
    current_index: int = 0
    iterations: int = 0


class SupervisorAgent(BaseAgent):
    """
    Supervisor agent that coordinates the multi-agent workflow
    Decides which agent should act next based on current state
    """

    def __init__(self):
        super().__init__(
            name="supervisor",
            model=settings.agent_supervisor_model
        )
        self.max_iterations = settings.agent_max_iterations

    async def execute(self, state: Dict[str, Any]) -> AgentResponse:
        """
        Determine next agent to execute based on workflow state
        
        Args:
            state: Current workflow state
            
        Returns:
            AgentResponse with next agent directive
        """
        self.log_execution("Evaluating workflow state")
        
        # Get or initialize workflow plan
        plan = state.get('workflow_plan')
        if not plan:
            plan = self._create_plan(state)
            state['workflow_plan'] = plan
        
        # Check for completion or max iterations
        if plan.iterations >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached")
            return AgentResponse(
                success=True,
                data={"action": "force_complete"},
                next_agent=AgentTask.RESPOND.value,
                message="Max iterations reached, forcing response"
            )
        
        # Determine next action
        next_task = self._determine_next_task(state, plan)
        plan.iterations += 1
        
        if next_task == AgentTask.COMPLETE:
            return AgentResponse(
                success=True,
                data={"action": "complete"},
                next_agent=None,
                message="Workflow complete"
            )
        
        if next_task == AgentTask.REFUSE:
            return AgentResponse(
                success=True,
                data={"action": "refuse"},
                next_agent="response",
                message="Insufficient evidence, refusing to answer"
            )
        
        return AgentResponse(
            success=True,
            data={"action": next_task.value},
            next_agent=next_task.value,
            message=f"Delegating to {next_task.value} agent"
        )

    def _create_plan(self, state: Dict[str, Any]) -> WorkflowPlan:
        """Create initial workflow plan based on query analysis"""
        query = state.get('query', '')
        
        # Standard workflow: retrieve -> validate -> reason -> respond
        tasks = [
            AgentTask.RETRIEVE,
            AgentTask.VALIDATE,
            AgentTask.REASON,
            AgentTask.RESPOND
        ]
        
        return WorkflowPlan(tasks=tasks)

    def _determine_next_task(
        self,
        state: Dict[str, Any],
        plan: WorkflowPlan
    ) -> AgentTask:
        """
        Determine which agent should act next
        
        Uses rule-based logic enhanced by LLM for complex decisions
        """
        # Check if we have retrieved documents
        documents = state.get('retrieved_documents', [])
        evidence_score = state.get('evidence_score', 0.0)
        validation_passed = state.get('validation_passed', None)
        has_response = state.get('final_response') is not None
        
        # Rule-based routing
        if has_response:
            return AgentTask.COMPLETE
        
        if not documents:
            # Need retrieval
            if state.get('retrieval_attempted', False):
                # Already tried retrieval, refuse
                return AgentTask.REFUSE
            return AgentTask.RETRIEVE
        
        if validation_passed is None:
            # Need validation
            return AgentTask.VALIDATE
        
        if not validation_passed:
            # Validation failed
            if evidence_score < settings.refusal_threshold:
                return AgentTask.REFUSE
            # Try to reason anyway with low confidence
            return AgentTask.REASON
        
        if state.get('reasoning_complete', False):
            return AgentTask.RESPOND
        
        # Default: proceed with reasoning
        return AgentTask.REASON

    async def should_continue(self, state: Dict[str, Any]) -> bool:
        """Check if workflow should continue"""
        plan = state.get('workflow_plan')
        if not plan:
            return True
        
        return (
            plan.iterations < self.max_iterations and
            state.get('final_response') is None
        )

    def get_workflow_status(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get current workflow status"""
        plan = state.get('workflow_plan')
        return {
            "iterations": plan.iterations if plan else 0,
            "max_iterations": self.max_iterations,
            "has_documents": len(state.get('retrieved_documents', [])) > 0,
            "validation_passed": state.get('validation_passed'),
            "reasoning_complete": state.get('reasoning_complete', False),
            "has_response": state.get('final_response') is not None
        }