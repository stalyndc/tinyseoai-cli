"""
Performance Agent - Specialist in website speed and Core Web Vitals.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional


from ..utils.logging import get_logger
from .base import AgentContext, BaseAgent
from .models import AgentProfile, AgentResult, AgentRole, AgentTask
from .prompts import PERFORMANCE_SYSTEM_PROMPT, format_performance_prompt

logger = get_logger(__name__)


class PerformanceAgent(BaseAgent):
    """
    Performance Agent specializes in website speed optimization.

    Expertise:
    - Image optimization
    - Render-blocking resources
    - Critical rendering path
    - Resource minification
    - Browser caching
    - Core Web Vitals
    """

    def __init__(self, context: Optional[AgentContext] = None, api_key: Optional[str] = None):
        profile = AgentProfile(
            role=AgentRole.PERFORMANCE,
            name="Performance Agent",
            description="Specialist in website speed and Core Web Vitals optimization",
            capabilities=[],
            specialization=["performance", "speed", "core-web-vitals", "optimization"],
            max_concurrent_tasks=3,
            default_model="gpt-4o-mini",
            fallback_models=["gpt-4o"],
        )
        super().__init__(profile, context, api_key)

    def _initialize_tools(self) -> List[Any]:
        """Initialize tools (simplified for LangChain 1.0)."""
        return []

    
    def _analyze_image_optimization(self, issues_json: str) -> str:
        """Analyze image optimization issues."""
        try:
            issues = json.loads(issues_json)
            image_issues = [
                i for i in issues if "image" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(image_issues),
                "recommendations": [
                    "Compress images to reduce file size without quality loss",
                    "Use modern image formats (WebP, AVIF) with fallbacks",
                    "Implement lazy loading for images below the fold",
                    "Specify image dimensions to prevent layout shifts",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing images: {e}"

    def _analyze_render_blocking(self, issues_json: str) -> str:
        """Analyze render-blocking resource issues."""
        try:
            issues = json.loads(issues_json)
            blocking_issues = [
                i for i in issues if "render" in i.get("type", "").lower() or "blocking" in i.get("type", "").lower()
            ]

            analysis = {
                "count": len(blocking_issues),
                "recommendations": [
                    "Defer non-critical JavaScript to improve page load time",
                    "Inline critical CSS and defer non-critical stylesheets",
                    "Minimize and bundle CSS/JS resources",
                ],
            }

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing render-blocking: {e}"

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute performance analysis task."""
        start_time = time.time()
        task.start()

        # Create chain of thought
        cot = self.create_chain_of_thought(
            task, goal="Analyze performance issues and provide speed optimization recommendations"
        )

        try:
            # Extract context
            issues = task.context.get("issues", [])
            site_url = task.context.get("site_url", "unknown")
            performance_data = task.context.get("performance_data", {})

            cot.add_step(
                "observation",
                f"Analyzing {len(issues)} performance issues for {site_url}",
                confidence=1.0,
                supporting_data={"issue_count": len(issues)},
            )

            # Format prompt
            prompt = format_performance_prompt(site_url, issues, performance_data)

            cot.add_step(
                "reflection",
                "Identifying performance bottlenecks affecting page speed and Core Web Vitals",
                confidence=0.95,
            )

            # Run analysis with chain of thought
            result_data = await self.reason_with_chain_of_thought(task, prompt, cot)

            # Extract insights
            insights = self._extract_performance_insights(issues)

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
            self._add_performance_recommendations(result, issues)

            # Update stats
            self.tasks_completed += 1
            self.total_execution_time_ms += result.execution_time_ms

            task.complete(result)
            logger.info(
                f"Performance Agent completed task {task.id} in {result.execution_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Performance task {task.id} failed: {e}")
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

    def _extract_performance_insights(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Extract performance insights."""
        insights = []

        # Image insights
        image_issues = [i for i in issues if "image" in i.get("type", "").lower()]
        if image_issues:
            insights.append(
                f"Performance Alert: {len(image_issues)} image optimization opportunities - can significantly improve load times"
            )

        # Render-blocking insights
        blocking_issues = [
            i for i in issues if "render" in i.get("type", "").lower() or "blocking" in i.get("type", "").lower()
        ]
        if blocking_issues:
            insights.append(
                f"Critical: {len(blocking_issues)} render-blocking resources - deferring these can improve Core Web Vitals"
            )

        return insights

    def _add_performance_recommendations(
        self, result: AgentResult, issues: List[Dict[str, Any]]
    ) -> None:
        """Add performance recommendations."""
        # Image optimization
        image_issues = [i for i in issues if "image" in i.get("type", "").lower()]
        if image_issues:
            result.add_recommendation(
                title="Optimize Images",
                description=f"Compress and optimize {len(image_issues)} images to reduce page weight and improve load times",
                priority="medium",
                impact=7.5,
                effort=4.0,
                category="performance",
            )

        # Render-blocking
        blocking_issues = [
            i for i in issues if "render" in i.get("type", "").lower() or "blocking" in i.get("type", "").lower()
        ]
        if blocking_issues:
            result.add_recommendation(
                title="Defer Render-Blocking Resources",
                description=f"Defer {len(blocking_issues)} render-blocking resources to improve initial page load",
                priority="high",
                impact=8.0,
                effort=5.0,
                category="performance",
            )
