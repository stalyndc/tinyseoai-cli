"""
Orchestrator Agent - Central coordinator for the multi-agent system.
"""

from __future__ import annotations

import json
import time
from typing import Any

from ..utils.logging import get_logger
from .base import AgentContext, BaseAgent
from .models import (
    AgentProfile,
    AgentResult,
    AgentRole,
    AgentTask,
    TaskPriority,
)
from .prompts import (
    format_orchestrator_planning_prompt,
)

logger = get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent coordinates all specialist agents.

    Responsibilities:
    - Analyze audit results and identify priority areas
    - Create and assign tasks to specialist agents
    - Monitor task execution and handle failures
    - Synthesize results from multiple agents
    - Generate final comprehensive recommendations
    """

    def __init__(self, context: AgentContext | None = None, api_key: str | None = None):
        profile = AgentProfile(
            role=AgentRole.ORCHESTRATOR,
            name="Orchestrator Agent",
            description="Central coordinator for multi-agent SEO analysis",
            capabilities=[],
            specialization=["coordination", "planning", "synthesis"],
            max_concurrent_tasks=10,
            default_model="gpt-4o",
            fallback_models=["gpt-4o-mini", "claude-3-5-sonnet-20241022"],
        )
        super().__init__(profile, context, api_key)

    def _initialize_tools(self) -> list[Any]:
        """Initialize tools (simplified for LangChain 1.0)."""
        return []


    def _analyze_audit_data(self, audit_json: str) -> str:
        """Analyze audit data and return summary statistics."""
        try:
            data = json.loads(audit_json)
            issues = data.get("issues", [])

            # Count by severity
            severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
            for issue in issues:
                severity = issue.get("severity", "info")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Count by category
            category_counts: dict[str, int] = {}
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                # Categorize by issue type
                if "https" in issue_type or "ssl" in issue_type or "security" in issue_type:
                    category = "technical_seo"
                elif (
                    "title" in issue_type
                    or "meta" in issue_type
                    or "heading" in issue_type
                    or "content" in issue_type
                ):
                    category = "content"
                elif "performance" in issue_type or "image" in issue_type or "speed" in issue_type:
                    category = "performance"
                elif "link" in issue_type or "redirect" in issue_type:
                    category = "links"
                else:
                    category = "other"

                category_counts[category] = category_counts.get(category, 0) + 1

            summary = {
                "total_issues": len(issues),
                "by_severity": severity_counts,
                "by_category": category_counts,
                "health_score": data.get("meta", {}).get("health_score", 0),
            }

            return json.dumps(summary, indent=2)

        except Exception as e:
            return f"Error analyzing audit data: {e}"

    def _categorize_issues(self, issues_json: str) -> str:
        """Categorize issues and map to specialist agents."""
        try:
            issues = json.loads(issues_json)

            agent_mapping = {
                "technical_seo": [],
                "content_quality": [],
                "performance": [],
                "link_analysis": [],
                "general": [],
            }

            for issue in issues:
                issue_type = issue.get("type", "unknown").lower()

                # Map to appropriate agent
                if any(
                    keyword in issue_type
                    for keyword in ["https", "ssl", "robots", "sitemap", "canonical", "security"]
                ):
                    agent_mapping["technical_seo"].append(issue)
                elif any(
                    keyword in issue_type
                    for keyword in ["title", "meta", "heading", "content", "duplicate", "readability"]
                ):
                    agent_mapping["content_quality"].append(issue)
                elif any(
                    keyword in issue_type
                    for keyword in ["performance", "image", "speed", "render", "cache"]
                ):
                    agent_mapping["performance"].append(issue)
                elif any(
                    keyword in issue_type for keyword in ["link", "broken", "redirect", "orphan"]
                ):
                    agent_mapping["link_analysis"].append(issue)
                else:
                    agent_mapping["general"].append(issue)

            # Create summary
            summary = {
                agent: {"count": len(issues_list), "sample": issues_list[:3]}
                for agent, issues_list in agent_mapping.items()
                if issues_list
            }

            return json.dumps(summary, indent=2)

        except Exception as e:
            return f"Error categorizing issues: {e}"

    def _create_execution_plan(self, analysis_json: str) -> str:
        """Create a structured execution plan."""
        try:
            json.loads(analysis_json)

            plan = {
                "phases": [
                    {
                        "name": "Technical Foundation",
                        "agents": ["technical_seo"],
                        "priority": "critical",
                        "rationale": "Fix crawlability and indexability issues first",
                    },
                    {
                        "name": "Content Optimization",
                        "agents": ["content_quality"],
                        "priority": "high",
                        "rationale": "Optimize on-page elements for better rankings",
                    },
                    {
                        "name": "Performance & Links",
                        "agents": ["performance", "link_analysis"],
                        "priority": "medium",
                        "rationale": "Improve site speed and internal linking",
                    },
                    {
                        "name": "Fix Generation",
                        "agents": ["fix_generator"],
                        "priority": "high",
                        "rationale": "Generate implementation code for all fixes",
                    },
                ],
                "estimated_duration_minutes": 10,
                "parallel_execution": True,
            }

            return json.dumps(plan, indent=2)

        except Exception as e:
            return f"Error creating execution plan: {e}"

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Execute orchestration task.

        The orchestrator analyzes audit data and creates a task distribution plan.
        """
        start_time = time.time()
        task.start()

        # Create chain of thought
        cot = self.create_chain_of_thought(
            task, goal="Analyze audit results and create execution plan for specialist agents"
        )

        try:
            # Get audit data from context
            if not self.context:
                raise ValueError("Orchestrator requires context to access audit data")

            audit_data = self.context.get_audit_data()

            cot.add_step(
                "observation",
                f"Received audit data for {audit_data.get('site', 'unknown')} "
                f"with {len(audit_data.get('issues', []))} issues",
                confidence=1.0,
                supporting_data={"issue_count": len(audit_data.get("issues", []))},
            )

            # Analyze the audit results
            prompt = format_orchestrator_planning_prompt(audit_data)

            cot.add_step(
                "planning",
                "Analyzing audit data to identify critical areas and agent assignments",
                confidence=0.95,
            )

            # Use LLM to create execution plan
            result_data = await self.reason_with_chain_of_thought(task, prompt, cot)

            # Extract insights
            insights = self._extract_insights(audit_data, result_data)

            # Create result
            result = AgentResult(
                task_id=task.id,
                agent_role=self.profile.role,
                success=True,
                data=result_data,
                insights=insights,
                chain_of_thought=cot,
                execution_time_ms=(time.time() - start_time) * 1000,
                model_used=self.profile.default_model,
                confidence=cot.confidence_score,
            )

            # Generate recommendations
            self._add_orchestration_recommendations(result, audit_data)

            # Update stats
            self.tasks_completed += 1
            self.total_execution_time_ms += result.execution_time_ms

            task.complete(result)
            logger.info(
                f"Orchestrator completed task {task.id} in {result.execution_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Orchestrator task {task.id} failed: {e}")
            cot.add_step("error", f"Task execution failed: {str(e)}", confidence=0.0)

            result = AgentResult(
                task_id=task.id,
                agent_role=self.profile.role,
                success=False,
                data={"error": str(e)},
                chain_of_thought=cot,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

            task.fail(str(e))
            return result

    def _extract_insights(
        self, audit_data: dict[str, Any], result_data: dict[str, Any]
    ) -> list[str]:
        """Extract key insights from orchestration analysis."""
        insights = []

        issues = audit_data.get("issues", [])
        health_score = audit_data.get("meta", {}).get("health_score", 0)

        # Overall health insight
        if health_score < 50:
            insights.append(
                f"Critical: Site health score is {health_score}/100 - immediate action required"
            )
        elif health_score < 70:
            insights.append(
                f"Warning: Site health score is {health_score}/100 - significant improvements needed"
            )

        # Count high severity issues
        high_severity = [i for i in issues if i.get("severity") == "high"]
        if high_severity:
            insights.append(
                f"Found {len(high_severity)} high-severity issues requiring immediate attention"
            )

        # Check for security issues
        security_issues = [
            i
            for i in issues
            if any(
                keyword in i.get("type", "").lower() for keyword in ["https", "ssl", "security"]
            )
        ]
        if security_issues:
            insights.append(
                f"Security concerns detected: {len(security_issues)} issues affecting site trustworthiness"
            )

        # Check for indexability issues
        indexability_issues = [
            i
            for i in issues
            if any(
                keyword in i.get("type", "").lower()
                for keyword in ["robots", "canonical", "index"]
            )
        ]
        if indexability_issues:
            insights.append(
                f"Indexability issues found: {len(indexability_issues)} problems may prevent proper indexing"
            )

        return insights

    def _add_orchestration_recommendations(
        self, result: AgentResult, audit_data: dict[str, Any]
    ) -> None:
        """Add orchestration-level recommendations."""
        issues = audit_data.get("issues", [])

        # Recommend specialist agent deployment
        agent_recommendations = {}

        for issue in issues:
            issue_type = issue.get("type", "").lower()

            # Map to agents
            if any(
                keyword in issue_type
                for keyword in ["https", "ssl", "robots", "sitemap", "canonical"]
            ):
                agent_recommendations.setdefault("technical_seo", []).append(issue)
            elif any(keyword in issue_type for keyword in ["title", "meta", "content"]):
                agent_recommendations.setdefault("content_quality", []).append(issue)
            elif any(keyword in issue_type for keyword in ["performance", "image", "speed"]):
                agent_recommendations.setdefault("performance", []).append(issue)
            elif any(keyword in issue_type for keyword in ["link", "broken", "redirect"]):
                agent_recommendations.setdefault("link_analysis", []).append(issue)

        # Create recommendations
        for agent, agent_issues in agent_recommendations.items():
            if len(agent_issues) >= 5:
                priority = "high"
                impact = 8.0
            elif len(agent_issues) >= 3:
                priority = "medium"
                impact = 6.0
            else:
                priority = "low"
                impact = 4.0

            result.add_recommendation(
                title=f"Deploy {agent.replace('_', ' ').title()} Agent",
                description=f"Analyze and fix {len(agent_issues)} issues in {agent} category",
                priority=priority,
                impact=impact,
                effort=3.0,
                agent=agent,
                issue_count=len(agent_issues),
            )

    def create_task_distribution_plan(
        self, audit_data: dict[str, Any]
    ) -> list[AgentTask]:
        """
        Create a list of tasks for specialist agents based on audit results.

        Returns:
            List of AgentTask objects ready for execution
        """
        tasks: list[AgentTask] = []
        issues = audit_data.get("issues", [])

        # Group issues by agent category
        technical_issues = []
        content_issues = []
        performance_issues = []
        link_issues = []

        for issue in issues:
            issue_type = issue.get("type", "").lower()

            if any(
                keyword in issue_type
                for keyword in ["https", "ssl", "robots", "sitemap", "canonical", "security"]
            ):
                technical_issues.append(issue)
            elif any(
                keyword in issue_type
                for keyword in ["title", "meta", "heading", "content", "duplicate"]
            ):
                content_issues.append(issue)
            elif any(
                keyword in issue_type for keyword in ["performance", "image", "speed", "render"]
            ):
                performance_issues.append(issue)
            elif any(keyword in issue_type for keyword in ["link", "broken", "redirect", "orphan"]):
                link_issues.append(issue)

        # Create tasks for each agent
        if technical_issues:
            tasks.append(
                AgentTask(
                    assigned_to=AgentRole.TECHNICAL_SEO,
                    priority=TaskPriority.CRITICAL,
                    title="Analyze Technical SEO Issues",
                    description=f"Analyze {len(technical_issues)} technical SEO issues including HTTPS, robots.txt, sitemaps, and security",
                    context={
                        "issues": technical_issues,
                        "site_url": audit_data.get("site"),
                        "metadata": audit_data.get("meta", {}),
                    },
                )
            )

        if content_issues:
            tasks.append(
                AgentTask(
                    assigned_to=AgentRole.CONTENT_QUALITY,
                    priority=TaskPriority.HIGH,
                    title="Analyze Content Quality Issues",
                    description=f"Analyze {len(content_issues)} content quality issues including titles, meta descriptions, and headings",
                    context={
                        "issues": content_issues,
                        "site_url": audit_data.get("site"),
                        "content_data": {},
                    },
                )
            )

        if performance_issues:
            tasks.append(
                AgentTask(
                    assigned_to=AgentRole.PERFORMANCE,
                    priority=TaskPriority.MEDIUM,
                    title="Analyze Performance Issues",
                    description=f"Analyze {len(performance_issues)} performance issues including image optimization and render-blocking resources",
                    context={
                        "issues": performance_issues,
                        "site_url": audit_data.get("site"),
                        "performance_data": {},
                    },
                )
            )

        if link_issues:
            tasks.append(
                AgentTask(
                    assigned_to=AgentRole.LINK_ANALYSIS,
                    priority=TaskPriority.MEDIUM,
                    title="Analyze Link Structure Issues",
                    description=f"Analyze {len(link_issues)} link-related issues including broken links and orphan pages",
                    context={
                        "issues": link_issues,
                        "site_url": audit_data.get("site"),
                        "link_graph_data": {},
                    },
                )
            )

        logger.info(f"Created {len(tasks)} tasks for specialist agents")
        return tasks
