"""
Base Agent class for Multi-Agent Architecture
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.reasoning.llm.ollama_reasoner import OllamaReasoner
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Standard response from an agent"""
    success: bool
    data: Dict[str, Any]
    next_agent: Optional[str] = None
    message: str = ""
    confidence: float = 1.0


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system
    """

    def __init__(self, name: str, model: Optional[str] = None):
        """
        Initialize base agent
        
        Args:
            name: Agent identifier
            model: Optional model override
        """
        self.name = name
        self.model = model or settings.agent_worker_model
        self.llm = OllamaReasoner(model=self.model)
        self.max_retries = 3

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> AgentResponse:
        """
        Execute the agent's task
        
        Args:
            state: Current workflow state
            
        Returns:
            AgentResponse with results
        """
        pass

    def _build_prompt(self, template: str, **kwargs) -> str:
        """Build prompt from template with variables"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return template

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response"""
        import json
        import re
        
        # Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Failed to parse JSON from response: {response[:100]}...")
        return None

    def log_execution(self, action: str, details: Dict[str, Any] = None):
        """Log agent execution details"""
        logger.info(f"[{self.name}] {action}")
        if details:
            for key, value in details.items():
                logger.debug(f"  {key}: {value}")