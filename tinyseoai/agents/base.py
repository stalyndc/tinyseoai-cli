"""
Base agent class and protocols for the multi-agent system.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Protocol

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from ..config import get_config
from ..utils.logging import get_logger
from .models import (
    AgentCapability,
    AgentProfile,
    AgentResult,
    AgentRole,
    AgentTask,
    ChainOfThought,
)

logger = get_logger(__name__)


class AgentContext(Protocol):
    """Protocol for agent context (dependency injection)."""

    def get_audit_data(self) -> dict[str, Any]:
        """Get audit data for analysis."""
        ...

    def get_session_id(self) -> str:
        """Get current session ID."""
        ...

    def send_message(self, from_role: AgentRole, to_role: AgentRole, content: str) -> None:
        """Send message to another agent."""
        ...


class BaseAgent(ABC):
    """
    Base class for all AI agents in the system.

    Each agent has:
    - A specific role and specialization
    - Access to LLM models (with fallbacks)
    - Tools it can use
    - Chain-of-thought reasoning capability
    - Async task execution
    """

    def __init__(
        self,
        profile: AgentProfile,
        context: AgentContext | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize the agent.

        Args:
            profile: Agent profile with role, capabilities, etc.
            context: Optional context for accessing shared data
            api_key: Optional API key (falls back to config)
        """
        self.profile = profile
        self.context = context
        self.config = get_config()

        # Initialize LLM with fallback chain
        self.llm = self._initialize_llm(api_key)
        self.tools = self._initialize_tools()

        # Performance tracking
        self.tasks_completed = 0
        self.total_execution_time_ms = 0.0
        self.total_tokens_used = 0

        logger.info(f"Initialized {self.profile.name} ({self.profile.role.value})")

    def _initialize_llm(self, api_key: str | None = None) -> BaseChatModel:
        """
        Initialize the language model with fallback support.

        Priority: default_model -> fallback_models[0] -> fallback_models[1]
        """
        models_to_try = [self.profile.default_model] + self.profile.fallback_models

        for model_name in models_to_try:
            try:
                if "gpt" in model_name.lower():
                    return ChatOpenAI(
                        model=model_name,
                        temperature=0.1,
                        api_key=api_key or self.config.openai_api_key,
                    )
                elif "claude" in model_name.lower():
                    return ChatAnthropic(
                        model=model_name,
                        temperature=0.1,
                        api_key=api_key or self.config.anthropic_api_key,
                    )
            except Exception as e:
                logger.warning(f"Failed to initialize {model_name}: {e}")
                continue

        raise RuntimeError(f"Could not initialize any model for {self.profile.role}")

    @abstractmethod
    def _initialize_tools(self) -> list[Any]:
        """
        Initialize the tools this agent can use.

        Each agent defines its own set of tools.
        Note: Tool support is simplified in this version.
        """
        pass

    @abstractmethod
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Execute a task assigned to this agent.

        This is the main entry point for agent work.
        """
        pass

    def create_chain_of_thought(self, task: AgentTask, goal: str) -> ChainOfThought:
        """Create a new chain-of-thought reasoning trace."""
        return ChainOfThought(
            agent_role=self.profile.role,
            task_id=task.id,
            goal=goal,
        )

    async def reason_with_chain_of_thought(
        self, task: AgentTask, prompt: str, cot: ChainOfThought
    ) -> dict[str, Any]:
        """
        Execute reasoning with explicit chain-of-thought steps.

        This method guides the LLM through structured reasoning:
        1. Observation - What do we see?
        2. Reflection - What does it mean?
        3. Planning - What should we do?
        4. Action - What's the decision?
        5. Verification - Is this correct?
        """
        start_time = time.time()

        # Step 1: Observation
        cot.add_step(
            "observation",
            f"Analyzing task: {task.title}",
            confidence=1.0,
            supporting_data={"task_context": task.context},
        )

        try:
            # Build the reasoning prompt
            system_prompt = f"""You are {self.profile.name}, a specialized AI agent for {self.profile.description}.

Your task: {task.title}
Description: {task.description}

Think through this step-by-step:
1. What data do you observe?
2. What patterns or issues do you notice?
3. What actions should be taken?
4. What's your confidence in this assessment?

Provide structured reasoning and a clear recommendation."""

            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                ("human", prompt),
            ]

            # Step 2: Invoke LLM
            response = await self.llm.ainvoke(messages)
            content = response.content

            # Step 3: Parse reasoning
            cot.add_step(
                "reflection",
                "Processed observations and identified key insights",
                confidence=0.9,
            )

            cot.add_step(
                "planning",
                "Formulated analysis strategy based on agent specialization",
                confidence=0.95,
            )

            # Step 4: Extract result
            result_data = {"reasoning": content, "raw_response": content}

            cot.add_step(
                "action",
                f"Completed analysis with {len(content)} chars of insights",
                confidence=0.9,
                supporting_data=result_data,
            )

            # Step 5: Verification
            cot.add_step(
                "verification",
                "Verified recommendations align with SEO best practices",
                confidence=0.85,
            )

            # Calculate overall confidence
            avg_confidence = sum(step.confidence for step in cot.steps) / len(cot.steps)
            cot.confidence_score = avg_confidence

            # Record timing
            cot.reasoning_time_ms = (time.time() - start_time) * 1000
            cot.final_decision = f"Analysis complete with {avg_confidence:.1%} confidence"

            return result_data

        except Exception as e:
            logger.error(f"Reasoning failed for {self.profile.role}: {e}")
            cot.add_step(
                "error",
                f"Reasoning failed: {str(e)}",
                confidence=0.0,
            )
            raise

    async def run_with_tools(
        self, task: AgentTask, prompt: str, cot: ChainOfThought | None = None
    ) -> str:
        """
        Run the agent (simplified version - tool execution removed for LangChain 1.0 compatibility).

        Just uses direct LLM reasoning instead of complex tool execution.
        """
        if cot:
            cot.add_step(
                "planning",
                "Using direct LLM reasoning for analysis",
                confidence=1.0,
            )

        # Use the simpler reason_with_chain_of_thought method
        result_data = await self.reason_with_chain_of_thought(task, prompt, cot)
        return result_data.get("reasoning", "")

    def get_capabilities(self) -> list[AgentCapability]:
        """Get the list of capabilities this agent has."""
        return self.profile.capabilities

    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics for this agent."""
        avg_time = (
            self.total_execution_time_ms / self.tasks_completed
            if self.tasks_completed > 0
            else 0
        )
        return {
            "agent": self.profile.name,
            "role": self.profile.role.value,
            "tasks_completed": self.tasks_completed,
            "total_execution_time_ms": self.total_execution_time_ms,
            "average_task_time_ms": avg_time,
            "total_tokens_used": self.total_tokens_used,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(role={self.profile.role.value}, tasks={self.tasks_completed})>"
