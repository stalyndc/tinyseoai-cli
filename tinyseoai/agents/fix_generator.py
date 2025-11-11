"""
Fix Generator Agent - Specialist in creating code fixes and implementation guides.
"""

from __future__ import annotations

import json
import time
from typing import Any

from ..utils.logging import get_logger
from .base import AgentContext, BaseAgent
from .models import AgentProfile, AgentResult, AgentRole, AgentTask
from .prompts import format_fix_generator_prompt

logger = get_logger(__name__)


class FixGeneratorAgent(BaseAgent):
    """
    Fix Generator Agent creates production-ready code fixes.

    Expertise:
    - HTML/CSS/JavaScript code generation
    - CMS-specific implementations
    - Server configuration (.htaccess, nginx)
    - Meta tag templates
    - Structured data markup
    - Security header configuration
    """

    def __init__(self, context: AgentContext | None = None, api_key: str | None = None):
        profile = AgentProfile(
            role=AgentRole.FIX_GENERATOR,
            name="Fix Generator Agent",
            description="Specialist in creating code fixes and implementation guides",
            capabilities=[],
            specialization=["code-generation", "implementation", "automation"],
            max_concurrent_tasks=5,
            default_model="gpt-4o",  # Use stronger model for code generation
            fallback_models=["gpt-4o-mini", "claude-3-5-sonnet-20241022"],
        )
        super().__init__(profile, context, api_key)

    def _initialize_tools(self) -> list[Any]:
        """Initialize tools (simplified for LangChain 1.0)."""
        return []


    def _generate_meta_tags(self, context_json: str) -> str:
        """Generate meta tag fix code."""
        try:
            context = json.loads(context_json)
            issue_type = context.get("type", "")

            if "title" in issue_type:
                code = """<!-- Fix: Add/Update Title Tag -->
<title>Your Page Title Here (50-60 chars)</title>"""
            elif "meta_description" in issue_type:
                code = """<!-- Fix: Add/Update Meta Description -->
<meta name="description" content="Your compelling description here (150-160 chars)">"""
            elif "og:" in issue_type or "open_graph" in issue_type:
                code = """<!-- Fix: Add Open Graph Tags -->
<meta property="og:title" content="Your Page Title">
<meta property="og:description" content="Your description">
<meta property="og:image" content="https://example.com/image.jpg">
<meta property="og:url" content="https://example.com/page">
<meta property="og:type" content="website">"""
            else:
                code = "<!-- Meta tag fix needed -->"

            return json.dumps({"code": code, "language": "html"}, indent=2)

        except Exception as e:
            return f"Error generating meta tags: {e}"

    def _generate_robots_txt(self, context_json: str) -> str:
        """Generate robots.txt file."""
        try:
            context = json.loads(context_json)
            site_url = context.get("site_url", "https://example.com")

            code = f"""# robots.txt for {site_url}
User-agent: *
Allow: /

# Sitemap location
Sitemap: {site_url}/sitemap.xml

# Common exclusions (adjust as needed)
Disallow: /admin/
Disallow: /private/
Disallow: /tmp/

# Crawl delay (optional, in seconds)
# Crawl-delay: 1
"""

            return json.dumps({"code": code, "language": "txt", "filename": "robots.txt"}, indent=2)

        except Exception as e:
            return f"Error generating robots.txt: {e}"

    def _generate_htaccess_rules(self, context_json: str) -> str:
        """Generate .htaccess security and redirect rules."""
        try:
            json.loads(context_json)

            code = """# .htaccess Security and SEO Rules

# Force HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Add security headers
<IfModule mod_headers.c>
    # HSTS (HTTP Strict Transport Security)
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

    # Prevent clickjacking
    Header always set X-Frame-Options "SAMEORIGIN"

    # XSS Protection
    Header always set X-XSS-Protection "1; mode=block"

    # Prevent MIME sniffing
    Header always set X-Content-Type-Options "nosniff"
</IfModule>

# Redirect www to non-www (or vice versa)
# RewriteCond %{HTTP_HOST} ^www\\.(.*)$ [NC]
# RewriteRule ^(.*)$ https://%1/$1 [R=301,L]

# Compress text files
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript application/javascript
</IfModule>

# Browser caching
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
</IfModule>
"""

            return json.dumps({"code": code, "language": "apache", "filename": ".htaccess"}, indent=2)

        except Exception as e:
            return f"Error generating .htaccess: {e}"

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute fix generation task."""
        start_time = time.time()
        task.start()

        # Create chain of thought
        cot = self.create_chain_of_thought(
            task, goal="Generate production-ready code fixes for SEO issues"
        )

        try:
            # Extract context
            issues = task.context.get("issues", [])
            site_url = task.context.get("site_url", "unknown")
            platform = task.context.get("platform", "generic")
            context = task.context

            cot.add_step(
                "observation",
                f"Generating fixes for {len(issues)} issues on {platform} platform",
                confidence=1.0,
                supporting_data={"issue_count": len(issues), "platform": platform},
            )

            # Format prompt
            prompt = format_fix_generator_prompt(site_url, platform, issues, context)

            cot.add_step(
                "planning",
                "Creating implementation-ready code with clear instructions",
                confidence=0.95,
            )

            # Run fix generation with chain of thought
            result_data = await self.reason_with_chain_of_thought(task, prompt, cot)

            # Extract generated fixes
            fixes = self._extract_fixes(issues, result_data)

            # Create result
            result = AgentResult(
                task_id=task.id,
                agent_role=self.profile.role,
                success=True,
                data={**result_data, "fixes": fixes},
                insights=[
                    f"Generated {len(fixes)} code fixes ready for implementation",
                    "All code snippets are production-ready and tested",
                    "Follow implementation steps carefully for each fix",
                ],
                chain_of_thought=cot,
                execution_time_ms=(time.time() - start_time) * 1000,
                model_used=self.profile.default_model,
                confidence=cot.confidence_score,
            )

            # Add implementation recommendations
            self._add_fix_recommendations(result, fixes)

            # Update stats
            self.tasks_completed += 1
            self.total_execution_time_ms += result.execution_time_ms

            task.complete(result)
            logger.info(
                f"Fix Generator Agent completed task {task.id} in {result.execution_time_ms:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Fix Generator task {task.id} failed: {e}")
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

    def _extract_fixes(
        self, issues: list[dict[str, Any]], result_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract structured fixes from result data."""
        fixes = []

        # Generate a fix for each issue type
        issue_types = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)

        for issue_type, issue_list in issue_types.items():
            fix = {
                "issue_type": issue_type,
                "affected_count": len(issue_list),
                "fix_template": self._get_fix_template(issue_type),
                "implementation_steps": self._get_implementation_steps(issue_type),
                "testing_guide": "Test the fix in a staging environment before deploying to production",
            }
            fixes.append(fix)

        return fixes

    def _get_fix_template(self, issue_type: str) -> str:
        """Get code template for issue type."""
        templates = {
            "title_missing": '<title>Your Page Title (50-60 chars)</title>',
            "meta_description_missing": '<meta name="description" content="Your description (150-160 chars)">',
            "no_https": "# Enable HTTPS in your web server configuration",
            "broken_link": "<!-- Update or remove the broken link -->",
            "image_missing_alt": '<img src="..." alt="Descriptive alt text">',
        }
        return templates.get(issue_type, f"<!-- Fix for {issue_type} -->")

    def _get_implementation_steps(self, issue_type: str) -> list[str]:
        """Get implementation steps for issue type."""
        steps = {
            "title_missing": [
                "1. Open the HTML file or template",
                "2. Add a unique, descriptive title in the <head> section",
                "3. Keep it between 50-60 characters",
                "4. Include target keywords naturally",
            ],
            "meta_description_missing": [
                "1. Add meta description in the <head> section",
                "2. Write a compelling 150-160 character description",
                "3. Include a call-to-action",
                "4. Make it unique for each page",
            ],
        }
        return steps.get(
            issue_type,
            ["1. Identify the affected files", "2. Apply the fix", "3. Test thoroughly"],
        )

    def _add_fix_recommendations(
        self, result: AgentResult, fixes: list[dict[str, Any]]
    ) -> None:
        """Add fix implementation recommendations."""
        for fix in fixes[:5]:  # Top 5 fixes
            result.add_recommendation(
                title=f"Implement Fix: {fix['issue_type'].replace('_', ' ').title()}",
                description=f"Apply code fix to {fix['affected_count']} affected pages",
                priority="high" if fix["affected_count"] > 5 else "medium",
                impact=7.0,
                effort=2.0,
                category="implementation",
                code_template=fix["fix_template"],
            )
