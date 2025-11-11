"""
Link Analysis Agent - Specialist in internal link structure and link graph optimization.
"""

from __future__ import annotations

import json
import time
from typing import Any

from ..utils.logging import get_logger
from .base import AgentContext, BaseAgent
from .models import AgentProfile, AgentResult, AgentRole, AgentTask
from .prompts import format_link_analysis_prompt

logger = get_logger(__name__)


class LinkAnalysisAgent(BaseAgent):
    """
    Link Analysis Agent specializes in link structure optimization.

    Expertise:
    - Internal link graph analysis
    - Broken link detection
    - Orphan page identification
    - Anchor text optimization
    - Redirect chain analysis
    - Site architecture
    """

    def __init__(self, context: AgentContext | None = None, api_key: str | None = None):
        profile = AgentProfile(
            role=AgentRole.LINK_ANALYSIS,
            name="Link Analysis Agent",
            description="Specialist in internal link structure and link graph optimization",
            capabilities=[],
            specialization=["links", "site-architecture", "crawlability", "link-equity"],
            max_concurrent_tasks=3,
            default_model="gpt-4o-mini",
            fallback_models=["gpt-4o"],
        )
        super().__init__(profile, context, api_key)

    def _initialize_tools(self) -> list[Any]:
        """Initialize tools (simplified for LangChain 1.0)."""
        return []


    def _analyze_broken_links(self, issues_json: str) -> str:
        """Analyze broken link issues."""
        try:
            issues = json.loads(issues_json)
            broken_links = [
                i for i in issues if "broken" in i.get("type", "").lower() or "404" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(broken_links),
                "recommendations": [
                    "Fix or remove broken links to improve user experience",
                    "Update links pointing to moved content",
                    "Implement 301 redirects for permanently moved pages",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing broken links: {e}"

    def _analyze_orphan_pages(self, issues_json: str) -> str:
        """Analyze orphan page issues."""
        try:
            issues = json.loads(issues_json)
            orphan_issues = [
                i for i in issues if "orphan" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(orphan_issues),
                "recommendations": [
                    "Add internal links to orphan pages from relevant content",
                    "Include orphan pages in navigation or sitemap",
                    "Consider if orphan pages should be kept or removed",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing orphan pages: {e}"

    def _analyze_redirects(self, issues_json: str) -> str:
        """Analyze redirect chain issues."""
        try:
            issues = json.loads(issues_json)
            redirect_issues = [
                i for i in issues if "redirect" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(redirect_issues),
                "recommendations": [
                    "Reduce redirect chains to maximum 1-2 hops",
                    "Fix redirect loops that prevent page access",
                    "Use 301 redirects for permanent moves",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing redirects: {e}"

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute link analysis task."""
        start_time = time.time()
        task.start()

        # Create chain of thought
        cot = self.create_chain_of_thought(
            task, goal="Analyze link structure and provide architecture optimization recommendations"
        )

        try:
            # Extract context
            issues = task.context.get("issues", [])
            site_url = task.context.get("site_url", "unknown")
            link_graph_data = task.context.get("link_graph_data", {})

            cot.add_step(
                "observation",
                f"Analyzing {len(issues)} link-related issues for {site_url}",
                confidence=1.0,
                supporting_data={"issue_count": len(issues)},
            )

            # Format prompt
            prompt = format_link_analysis_prompt(site_url, issues, link_graph_data)

            cot.add_step(
                "reflection",
                "Identifying link structure problems affecting crawlability and PageRank distribution",
                confidence=0.95,
            )

            # Run analysis with chain of thought
            result_data = await self.reason_with_chain_of_thought(task, prompt, cot)

            # Extract insights
            insights = self._extract_link_insights(issues)

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

            # Add recommendations
            self._add_link_recommendations(result, issues)

            # Update stats
            self.tasks_completed += 1
            self.total_execution_time_ms += result.execution_time_ms

            task.complete(result)
            logger.info(
                f"Link Analysis Agent completed task {task.id} in {result.execution_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Link Analysis task {task.id} failed: {e}")
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

    def _extract_link_insights(self, issues: list[dict[str, Any]]) -> list[str]:
        """Extract link analysis insights."""
        insights = []

        # Broken links
        broken_links = [
            i for i in issues if "broken" in i.get("type", "").lower() or "404" in i.get("type", "").lower()
        ]
        if broken_links:
            insights.append(
                f"Link Alert: {len(broken_links)} broken links found - fix these to improve user experience and SEO"
            )

        # Orphan pages
        orphan_issues = [i for i in issues if "orphan" in i.get("type", "").lower()]
        if orphan_issues:
            insights.append(
                f"Architecture Issue: {len(orphan_issues)} orphan pages - these pages have no internal links and may not be crawled"
            )

        # Redirects
        redirect_issues = [i for i in issues if "redirect" in i.get("type", "").lower()]
        if redirect_issues:
            insights.append(
                f"Found {len(redirect_issues)} redirect issues - chains and loops slow down crawling"
            )

        return insights

    def _add_link_recommendations(
        self, result: AgentResult, issues: list[dict[str, Any]]
    ) -> None:
        """Add link optimization recommendations."""
        # Broken links
        broken_links = [
            i for i in issues if "broken" in i.get("type", "").lower() or "404" in i.get("type", "").lower()
        ]
        if broken_links:
            result.add_recommendation(
                title="Fix Broken Links",
                description=f"Repair or remove {len(broken_links)} broken links to improve user experience",
                priority="high",
                impact=7.0,
                effort=3.0,
                category="links",
            )

        # Orphan pages
        orphan_issues = [i for i in issues if "orphan" in i.get("type", "").lower()]
        if orphan_issues:
            result.add_recommendation(
                title="Connect Orphan Pages",
                description=f"Add internal links to {len(orphan_issues)} orphan pages to improve crawlability",
                priority="medium",
                impact=6.0,
                effort=4.0,
                category="site-architecture",
            )

        # Redirects
        redirect_issues = [i for i in issues if "redirect" in i.get("type", "").lower()]
        if redirect_issues:
            result.add_recommendation(
                title="Optimize Redirect Chains",
                description=f"Simplify {len(redirect_issues)} redirect chains to improve page load speed",
                priority="medium",
                impact=5.5,
                effort=3.0,
                category="links",
            )
