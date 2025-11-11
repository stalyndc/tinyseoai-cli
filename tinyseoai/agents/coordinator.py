# Copyright (c) 2025 Stalyn Disla
# Licensed under the MIT License

"""
Multi-agent coordinator for running SEO analysis with specialist agents.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ..data.models import AuditResult
from ..utils.logging import get_logger
from .base import AgentContext
from .content_quality import ContentQualityAgent
from .fix_generator import FixGeneratorAgent
from .link_analysis import LinkAnalysisAgent
from .models import (
    AgentMessage,
    AgentRole,
    AgentTask,
    MultiAgentSession,
    TaskStatus,
)
from .orchestrator import OrchestratorAgent
from .performance import PerformanceAgent
from .technical_seo import TechnicalSEOAgent

logger = get_logger(__name__)


class SimpleAgentContext:
    """Simple implementation of AgentContext for dependency injection."""

    def __init__(self, audit_data: dict[str, Any], session_id: str):
        self._audit_data = audit_data
        self._session_id = session_id
        self._messages: list[AgentMessage] = []

    def get_audit_data(self) -> dict[str, Any]:
        """Get audit data for analysis."""
        return self._audit_data

    def get_session_id(self) -> str:
        """Get current session ID."""
        return self._session_id

    def send_message(
        self, from_role: AgentRole, to_role: AgentRole, content: str
    ) -> None:
        """Send message to another agent."""
        message = AgentMessage(
            type="notification", from_agent=from_role, to_agent=to_role, content=content
        )
        self._messages.append(message)
        logger.debug(f"Message from {from_role.value} to {to_role.value}: {content[:50]}...")


class MultiAgentCoordinator:
    """
    Coordinates multiple AI agents for comprehensive SEO analysis.

    The coordinator:
    1. Initializes all specialist agents
    2. Creates and distributes tasks based on audit results
    3. Monitors task execution
    4. Collects and synthesizes results
    5. Generates comprehensive recommendations
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
    ):
        """
        Initialize the multi-agent coordinator.

        Args:
            openai_api_key: OpenAI API key for GPT models
            anthropic_api_key: Anthropic API key for Claude models
        """
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key

        # Agents will be initialized per session
        self.agents: dict[AgentRole, Any] = {}

        logger.info("Multi-agent coordinator initialized")

    def _initialize_agents(
        self, context: AgentContext
    ) -> dict[AgentRole, Any]:
        """Initialize all specialist agents."""
        agents = {
            AgentRole.ORCHESTRATOR: OrchestratorAgent(context, self.openai_api_key),
            AgentRole.TECHNICAL_SEO: TechnicalSEOAgent(context, self.openai_api_key),
            AgentRole.CONTENT_QUALITY: ContentQualityAgent(context, self.openai_api_key),
            AgentRole.PERFORMANCE: PerformanceAgent(context, self.openai_api_key),
            AgentRole.LINK_ANALYSIS: LinkAnalysisAgent(context, self.openai_api_key),
            AgentRole.FIX_GENERATOR: FixGeneratorAgent(context, self.openai_api_key),
        }

        logger.info(f"Initialized {len(agents)} specialist agents")
        return agents

    async def analyze_with_agents(
        self, audit_result: AuditResult, enable_fix_generation: bool = True
    ) -> dict[str, Any]:
        """
        Run multi-agent analysis on audit results.

        Args:
            audit_result: The SEO audit results to analyze
            enable_fix_generation: Whether to generate code fixes

        Returns:
            Dictionary containing agent analysis results and recommendations
        """
        logger.info(
            f"Starting multi-agent analysis for {audit_result.site} "
            f"({len(audit_result.issues)} issues)"
        )

        # Convert audit result to dict for context
        audit_data = {
            "site": audit_result.site,
            "pages_scanned": audit_result.pages_scanned,
            "issues": [issue.model_dump() for issue in audit_result.issues],
            "meta": audit_result.meta,
        }

        # Create session
        session = MultiAgentSession(
            site_url=audit_result.site,
            initiated_by=AgentRole.ORCHESTRATOR,
        )

        # Create context
        context = SimpleAgentContext(audit_data, session.id)

        # Initialize agents
        self.agents = self._initialize_agents(context)

        # Phase 1: Orchestrator creates task distribution plan
        logger.info("Phase 1: Orchestrator analyzing and creating task plan")
        orchestrator = self.agents[AgentRole.ORCHESTRATOR]

        orchestration_task = AgentTask(
            assigned_to=AgentRole.ORCHESTRATOR,
            priority="critical",
            title="Create Multi-Agent Execution Plan",
            description="Analyze audit results and distribute tasks to specialist agents",
            context=audit_data,
        )
        session.add_task(orchestration_task)

        orchestration_result = await orchestrator.execute_task(orchestration_task)
        session.record_result(orchestration_result)

        # Create tasks for specialist agents
        specialist_tasks = orchestrator.create_task_distribution_plan(audit_data)
        for task in specialist_tasks:
            session.add_task(task)

        logger.info(f"Created {len(specialist_tasks)} tasks for specialist agents")

        # Phase 2: Execute specialist agent tasks in parallel
        logger.info("Phase 2: Executing specialist agent tasks")
        specialist_results = await self._execute_specialist_tasks(
            specialist_tasks, enable_fix_generation
        )

        for result in specialist_results:
            session.record_result(result)

        # Phase 3: Optional fix generation
        if enable_fix_generation:
            logger.info("Phase 3: Generating code fixes")
            fix_result = await self._generate_fixes(audit_data, specialist_results)
            if fix_result:
                session.record_result(fix_result)

        # Mark session complete
        session.completed_at = orchestration_result.timestamp

        # Phase 4: Synthesize results
        logger.info("Phase 4: Synthesizing multi-agent analysis")
        synthesis = self._synthesize_results(session, orchestration_result, specialist_results)

        logger.info(
            f"Multi-agent analysis complete. Total tokens: {session.total_tokens}"
        )

        return synthesis

    async def _execute_specialist_tasks(
        self, tasks: list[AgentTask], include_fix_gen: bool
    ) -> list[Any]:
        """Execute specialist agent tasks in parallel."""
        # Group tasks by agent
        agent_tasks = {}
        for task in tasks:
            if task.assigned_to not in agent_tasks:
                agent_tasks[task.assigned_to] = []
            agent_tasks[task.assigned_to].append(task)

        # Execute tasks in parallel
        coroutines = []
        for agent_role, role_tasks in agent_tasks.items():
            if agent_role in self.agents:
                agent = self.agents[agent_role]
                for task in role_tasks:
                    coroutines.append(agent.execute_task(task))

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Agent task failed: {result}")
            else:
                valid_results.append(result)

        return valid_results

    async def _generate_fixes(
        self, audit_data: dict[str, Any], specialist_results: list[Any]
    ) -> Any | None:
        """Generate code fixes based on specialist recommendations."""
        try:
            fix_generator = self.agents[AgentRole.FIX_GENERATOR]

            # Collect all issues from specialist results
            all_issues = audit_data.get("issues", [])

            fix_task = AgentTask(
                assigned_to=AgentRole.FIX_GENERATOR,
                priority="high",
                title="Generate Code Fixes",
                description="Create production-ready code fixes for all identified issues",
                context={
                    "issues": all_issues[:20],  # Limit to top 20 issues
                    "site_url": audit_data.get("site"),
                    "platform": "generic",
                },
            )

            result = await fix_generator.execute_task(fix_task)
            return result

        except Exception as e:
            logger.error(f"Fix generation failed: {e}")
            return None

    def _synthesize_results(
        self,
        session: MultiAgentSession,
        orchestration_result: Any,
        specialist_results: list[Any],
    ) -> dict[str, Any]:
        """Synthesize all agent results into comprehensive analysis."""
        synthesis = {
            "session_id": session.id,
            "site_url": session.site_url,
            "total_tasks": len(session.tasks),
            "completed_tasks": len([t for t in session.tasks if t.status == TaskStatus.COMPLETED]),
            "total_tokens": session.total_tokens,
            "total_cost_usd": session.total_cost_usd,
            "orchestration": {
                "insights": orchestration_result.insights,
                "recommendations": orchestration_result.recommendations,
                "confidence": orchestration_result.confidence,
            },
            "specialist_analysis": {},
            "all_recommendations": [],
            "key_insights": [],
            "chain_of_thought_summary": [],
        }

        # Collect specialist results
        for result in specialist_results:
            agent_name = result.agent_role.value
            synthesis["specialist_analysis"][agent_name] = {
                "success": result.success,
                "insights": result.insights,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "execution_time_ms": result.execution_time_ms,
            }

            # Aggregate recommendations
            synthesis["all_recommendations"].extend(result.recommendations)

            # Aggregate insights
            synthesis["key_insights"].extend(result.insights)

            # Add chain of thought summary
            if result.chain_of_thought:
                synthesis["chain_of_thought_summary"].append(
                    {
                        "agent": agent_name,
                        "goal": result.chain_of_thought.goal,
                        "steps": len(result.chain_of_thought.steps),
                        "confidence": result.chain_of_thought.confidence_score,
                        "reasoning_time_ms": result.chain_of_thought.reasoning_time_ms,
                    }
                )

        # Sort recommendations by impact
        synthesis["all_recommendations"].sort(
            key=lambda x: x.get("impact", 0) * (1.0 / max(x.get("effort", 1), 0.1)),
            reverse=True,
        )

        # Get top 10 recommendations
        synthesis["top_recommendations"] = synthesis["all_recommendations"][:10]

        # Calculate average confidence
        confidences = [
            r.confidence for r in specialist_results if hasattr(r, "confidence")
        ]
        synthesis["average_confidence"] = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        return synthesis

    def get_agent_stats(self) -> dict[str, Any]:
        """Get performance statistics for all agents."""
        stats = {}
        for role, agent in self.agents.items():
            stats[role.value] = agent.get_stats()
        return stats
