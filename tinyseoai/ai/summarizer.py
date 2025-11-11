from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any

from ..config import get_config
from ..data.models import AuditResult, Issue
from .openai_client import call_ai_json


def _compact_issues(issues: list[Issue], limit_per_type: int = 5) -> dict[str, Any]:
    """
    Compress issues for prompt efficiency:
    - per-type counts
    - sample URLs (up to limit_per_type)
    """
    counts = Counter(i.type for i in issues)
    samples = defaultdict(list)
    for i in issues:
        if len(samples[i.type]) < limit_per_type:
            samples[i.type].append(i.url)

    return {
        "by_type_counts": counts,
        "by_type_samples": samples,
        "total": len(issues),
    }


def build_prompt(result: AuditResult) -> str:
    compact = _compact_issues(result.issues)
    payload = {
        "site": result.site,
        "pages_scanned": result.pages_scanned,
        "issues_compact": compact,
        "metrics_hint": {
            # Space for future numeric metrics if you add them later
        },
        "goal": "Create an executive summary for a client who is not deeply technical. "
                "Focus on impact and next steps."
    }
    # Keep it concise and deterministic
    instructions = """
Return STRICT JSON with this schema:
{
  "site": string,
  "summary": string,        // 2-3 sentences, plain language
  "top_issues": [           // 3-7 items
    {"type": string, "why_it_matters": string, "evidence": string}
  ],
  "recommended_actions": [  // 5-10 ordered steps
    {"action": string, "impact": "low|medium|high", "effort": "low|medium|high"}
  ],
  "quick_wins": [string],   // 3-5 quick, easy fixes
  "risk_items": [string]    // optional list, can be empty
}
Only include the JSON object. No commentary.
"""
    return instructions + "\nINPUT:\n" + json.dumps(payload, ensure_ascii=False)


def summarize_with_ai(result: AuditResult) -> dict[str, Any]:
    cfg = get_config()
    plan = cfg.plan  # 'free' or 'premium'

    prompt = build_prompt(result)
    data = call_ai_json(
        prompt=prompt,
        plan=plan,
        system="You are an expert technical SEO who writes concise, client-ready summaries.",
        temperature=0.2,
    )
    # Attach plan + model info for traceability (optional)
    data["plan_used"] = plan
    return data
