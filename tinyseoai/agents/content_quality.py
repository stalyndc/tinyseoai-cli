"""
Content Quality Agent - Specialist in on-page SEO and content optimization.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional


from ..utils.logging import get_logger
from .base import AgentContext, BaseAgent
from .models import AgentProfile, AgentResult, AgentRole, AgentTask
from .prompts import CONTENT_QUALITY_SYSTEM_PROMPT, format_content_quality_prompt

logger = get_logger(__name__)


class ContentQualityAgent(BaseAgent):
    """
    Content Quality Agent specializes in on-page SEO and content.

    Expertise:
    - Title tag optimization
    - Meta descriptions
    - Heading hierarchy
    - Content readability
    - Duplicate content detection
    - Image alt text
    - Keyword optimization
    """

    def __init__(self, context: Optional[AgentContext] = None, api_key: Optional[str] = None):
        profile = AgentProfile(
            role=AgentRole.CONTENT_QUALITY,
            name="Content Quality Agent",
            description="Specialist in on-page SEO and content optimization",
            capabilities=[],
            specialization=["content", "on-page", "copywriting", "user-experience"],
            max_concurrent_tasks=3,
            default_model="gpt-4o-mini",
            fallback_models=["gpt-4o", "claude-3-5-sonnet-20241022"],
        )
        super().__init__(profile, context, api_key)

    def _initialize_tools(self) -> List[Any]:
        """Initialize tools (simplified for LangChain 1.0)."""
        return []

    
    def _analyze_title_tags(self, issues_json: str) -> str:
        """Analyze title tag issues."""
        try:
            issues = json.loads(issues_json)
            title_issues = [
                i for i in issues if "title" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(title_issues),
                "missing": len([i for i in title_issues if "missing" in i.get("type", "").lower()]),
                "too_long": len([i for i in title_issues if "long" in i.get("type", "").lower()]),
                "recommendations": [
                    "Ensure every page has a unique, descriptive title tag",
                    "Keep titles between 50-60 characters for optimal display",
                    "Include target keywords naturally in titles",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing title tags: {e}"

    def _analyze_meta_descriptions(self, issues_json: str) -> str:
        """Analyze meta description issues."""
        try:
            issues = json.loads(issues_json)
            meta_issues = [
                i for i in issues if "meta" in i.get("type", "").lower() and "description" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(meta_issues),
                "recommendations": [
                    "Write compelling meta descriptions for all pages",
                    "Keep descriptions between 150-160 characters",
                    "Include a call-to-action to improve click-through rates",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing meta descriptions: {e}"

    def _analyze_headings(self, issues_json: str) -> str:
        """Analyze heading structure."""
        try:
            issues = json.loads(issues_json)
            heading_issues = [
                i for i in issues if "heading" in i.get("type", "").lower() or "h1" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(heading_issues),
                "recommendations": [
                    "Ensure each page has exactly one H1 tag",
                    "Maintain proper heading hierarchy (H1 -> H2 -> H3)",
                    "Include relevant keywords in headings naturally",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing headings: {e}"

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute content quality analysis task."""
        start_time = time.time()
        task.start()

        # Create chain of thought
        cot = self.create_chain_of_thought(
            task, goal="Analyze content quality issues and provide optimization recommendations"
        )

        try:
            # Extract context
            issues = task.context.get("issues", [])
            site_url = task.context.get("site_url", "unknown")
            content_data = task.context.get("content_data", {})

            cot.add_step(
                "observation",
                f"Analyzing {len(issues)} content quality issues for {site_url}",
                confidence=1.0,
                supporting_data={"issue_count": len(issues)},
            )

            # Format prompt
            prompt = format_content_quality_prompt(site_url, issues, content_data)

            cot.add_step(
                "reflection",
                "Identifying content optimization opportunities for better rankings and UX",
                confidence=0.95,
            )

            # Run analysis with chain of thought
            result_data = await self.reason_with_chain_of_thought(task, prompt, cot)

            # Extract insights
            insights = self._extract_content_insights(issues)

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
            self._add_content_recommendations(result, issues)

            # Update stats
            self.tasks_completed += 1
            self.total_execution_time_ms += result.execution_time_ms

            task.complete(result)
            logger.info(
                f"Content Quality Agent completed task {task.id} in {result.execution_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Content Quality task {task.id} failed: {e}")
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

    def _extract_content_insights(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Extract content quality insights."""
        insights = []

        # Title insights
        title_issues = [i for i in issues if "title" in i.get("type", "").lower()]
        if title_issues:
            insights.append(
                f"Content Alert: {len(title_issues)} title tag issues - titles are critical for rankings"
            )

        # Meta description insights
        meta_issues = [
            i for i in issues if "meta" in i.get("type", "").lower() and "description" in i.get("type", "").lower()
        ]
        if meta_issues:
            insights.append(
                f"Found {len(meta_issues)} meta description issues - improve click-through rates with better descriptions"
            )

        # Heading insights
        heading_issues = [i for i in issues if "heading" in i.get("type", "").lower() or "h1" in i.get("type", "").lower()]
        if heading_issues:
            insights.append(
                f"Structure Issue: {len(heading_issues)} heading problems - proper hierarchy improves SEO and readability"
            )

        return insights

    def _add_content_recommendations(
        self, result: AgentResult, issues: List[Dict[str, Any]]
    ) -> None:
        """Add content quality recommendations."""
        # Title recommendations
        title_issues = [i for i in issues if "title" in i.get("type", "").lower()]
        if title_issues:
            result.add_recommendation(
                title="Optimize Title Tags",
                description=f"Fix {len(title_issues)} title tag issues - ensure unique, descriptive titles on all pages",
                priority="high",
                impact=8.5,
                effort=3.0,
                category="content",
            )

        # Meta description recommendations
        meta_issues = [
            i for i in issues if "meta" in i.get("type", "").lower() and "description" in i.get("type", "").lower()
        ]
        if meta_issues:
            result.add_recommendation(
                title="Write Compelling Meta Descriptions",
                description=f"Add/improve {len(meta_issues)} meta descriptions to boost click-through rates",
                priority="medium",
                impact=6.5,
                effort=4.0,
                category="content",
            )

        # Heading recommendations
        heading_issues = [i for i in issues if "heading" in i.get("type", "").lower()]
        if heading_issues:
            result.add_recommendation(
                title="Fix Heading Structure",
                description=f"Correct {len(heading_issues)} heading hierarchy issues for better SEO and accessibility",
                priority="medium",
                impact=6.0,
                effort=2.0,
                category="content",
            )
