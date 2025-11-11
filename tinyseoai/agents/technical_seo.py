"""
Technical SEO Agent - Specialist in website technical infrastructure.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional


from ..utils.logging import get_logger
from .base import AgentContext, BaseAgent
from .models import AgentProfile, AgentResult, AgentRole, AgentTask
from .prompts import TECHNICAL_SEO_SYSTEM_PROMPT, format_technical_seo_prompt

logger = get_logger(__name__)


class TechnicalSEOAgent(BaseAgent):
    """
    Technical SEO Agent specializes in infrastructure and technical issues.

    Expertise:
    - HTTPS and SSL certificates
    - Robots.txt and crawl directives
    - XML sitemaps
    - Canonical tags
    - Structured data
    - Security headers
    - Indexability directives
    """

    def __init__(self, context: Optional[AgentContext] = None, api_key: Optional[str] = None):
        profile = AgentProfile(
            role=AgentRole.TECHNICAL_SEO,
            name="Technical SEO Agent",
            description="Specialist in website technical infrastructure and search engine optimization",
            capabilities=[],
            specialization=["technical", "security", "crawlability", "indexability"],
            max_concurrent_tasks=3,
            default_model="gpt-4o-mini",
            fallback_models=["gpt-4o", "claude-3-5-sonnet-20241022"],
        )
        super().__init__(profile, context, api_key)

    def _initialize_tools(self) -> List[Any]:
        """Initialize tools (simplified for LangChain 1.0)."""
        return []

    
    def _analyze_https_issues(self, issues_json: str) -> str:
        """Analyze HTTPS-related issues."""
        try:
            issues = json.loads(issues_json)
            https_issues = [
                i
                for i in issues
                if any(
                    keyword in i.get("type", "").lower() for keyword in ["https", "ssl", "security"]
                )
            ]

            analysis = {
                "count": len(https_issues),
                "critical": [i for i in https_issues if i.get("severity") == "high"],
                "recommendations": [],
            }

            if https_issues:
                analysis["recommendations"].append(
                    "Enable HTTPS site-wide to improve security and SEO rankings"
                )
                analysis["recommendations"].append("Ensure SSL certificate is valid and up-to-date")
                analysis["recommendations"].append(
                    "Implement HSTS header to enforce HTTPS connections"
                )

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing HTTPS issues: {e}"

    def _analyze_robots_txt(self, metadata_json: str) -> str:
        """Analyze robots.txt configuration."""
        try:
            metadata = json.loads(metadata_json)

            robots_exists = metadata.get("robots_txt_exists", False)
            sitemaps_found = metadata.get("sitemaps_found", 0)

            analysis = {
                "robots_txt_exists": robots_exists,
                "sitemaps_found": sitemaps_found,
                "recommendations": [],
            }

            if not robots_exists:
                analysis["recommendations"].append(
                    "Create a robots.txt file to guide search engine crawlers"
                )

            if sitemaps_found == 0:
                analysis["recommendations"].append(
                    "Add XML sitemap reference to robots.txt for better crawlability"
                )

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing robots.txt: {e}"

    def _analyze_indexability(self, issues_json: str) -> str:
        """Analyze indexability issues."""
        try:
            issues = json.loads(issues_json)
            indexability_issues = [
                i
                for i in issues
                if any(
                    keyword in i.get("type", "").lower()
                    for keyword in ["canonical", "robots", "index", "noindex"]
                )
            ]

            analysis = {
                "count": len(indexability_issues),
                "issues_by_type": {},
                "recommendations": [],
            }

            for issue in indexability_issues:
                issue_type = issue.get("type", "unknown")
                analysis["issues_by_type"][issue_type] = (
                    analysis["issues_by_type"].get(issue_type, 0) + 1
                )

            if indexability_issues:
                analysis["recommendations"].append(
                    "Review canonical tag implementation to avoid duplicate content issues"
                )
                analysis["recommendations"].append(
                    "Ensure important pages are not accidentally blocked by robots meta tags"
                )

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing indexability: {e}"

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute technical SEO analysis task."""
        start_time = time.time()
        task.start()

        # Create chain of thought
        cot = self.create_chain_of_thought(
            task, goal="Analyze technical SEO issues and provide actionable recommendations"
        )

        try:
            # Extract context
            issues = task.context.get("issues", [])
            site_url = task.context.get("site_url", "unknown")
            metadata = task.context.get("metadata", {})

            cot.add_step(
                "observation",
                f"Analyzing {len(issues)} technical SEO issues for {site_url}",
                confidence=1.0,
                supporting_data={"issue_count": len(issues)},
            )

            # Format prompt
            prompt = format_technical_seo_prompt(site_url, issues, metadata)

            cot.add_step(
                "reflection",
                "Identifying critical technical issues affecting crawlability and indexability",
                confidence=0.95,
            )

            # Run analysis with chain of thought
            result_data = await self.reason_with_chain_of_thought(task, prompt, cot)

            # Extract insights
            insights = self._extract_technical_insights(issues, metadata)

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
            self._add_technical_recommendations(result, issues, metadata)

            # Update stats
            self.tasks_completed += 1
            self.total_execution_time_ms += result.execution_time_ms

            task.complete(result)
            logger.info(
                f"Technical SEO Agent completed task {task.id} in {result.execution_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Technical SEO task {task.id} failed: {e}")
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

    def _extract_technical_insights(
        self, issues: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> List[str]:
        """Extract technical SEO insights."""
        insights = []

        # HTTPS insights
        https_issues = [
            i
            for i in issues
            if any(keyword in i.get("type", "").lower() for keyword in ["https", "ssl"])
        ]
        if https_issues:
            insights.append(
                f"Security Alert: {len(https_issues)} HTTPS/SSL issues detected - may affect rankings and user trust"
            )

        # Robots.txt insights
        if not metadata.get("robots_txt_exists"):
            insights.append(
                "Missing robots.txt file - search engines may not crawl your site efficiently"
            )

        # Sitemap insights
        if metadata.get("sitemaps_found", 0) == 0:
            insights.append(
                "No XML sitemaps detected - adding sitemaps helps search engines discover all pages"
            )

        return insights

    def _add_technical_recommendations(
        self, result: AgentResult, issues: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> None:
        """Add technical SEO recommendations."""
        # HTTPS recommendation
        https_issues = [
            i
            for i in issues
            if any(keyword in i.get("type", "").lower() for keyword in ["https", "ssl"])
        ]
        if https_issues:
            result.add_recommendation(
                title="Enable HTTPS Site-Wide",
                description=f"Fix {len(https_issues)} HTTPS/SSL issues to improve security and SEO",
                priority="critical",
                impact=9.0,
                effort=7.0,
                category="security",
            )

        # Robots.txt recommendation
        if not metadata.get("robots_txt_exists"):
            result.add_recommendation(
                title="Create robots.txt File",
                description="Add robots.txt to guide search engine crawlers and reference sitemaps",
                priority="high",
                impact=7.0,
                effort=2.0,
                category="crawlability",
            )

        # Sitemap recommendation
        if metadata.get("sitemaps_found", 0) == 0:
            result.add_recommendation(
                title="Add XML Sitemap",
                description="Create and submit XML sitemap to help search engines discover all pages",
                priority="high",
                impact=8.0,
                effort=3.0,
                category="crawlability",
            )
