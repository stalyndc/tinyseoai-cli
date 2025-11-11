from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from ..config import get_config


class AIError(RuntimeError):
    pass


@dataclass
class ModelChoice:
    """Holds resolved model ids for free/premium."""
    free: str
    premium: str


class AIConfig(BaseModel):
    model_free: str
    model_premium: str
    max_output_tokens: int = 800


def _load_api_key() -> str:
    # Load .env once; ignore if not present
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise AIError(
            "OPENAI_API_KEY is not set. Create a .env with OPENAI_API_KEY=sk-***"
        )
    return key


def resolve_models() -> ModelChoice:
    cfg = get_config()
    return ModelChoice(
        free=cfg.openai_model_free,
        premium=cfg.openai_model_premium,
    )


def get_client() -> OpenAI:
    key = _load_api_key()
    # The SDK reads from env automatically, but we also pass api_key for clarity
    return OpenAI(api_key=key)


def call_ai_json(
    prompt: str,
    plan: str = "free",
    system: Optional[str] = None,
    temperature: float = 0.2,
    max_output_tokens: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calls OpenAI Chat Completions API and returns parsed JSON.
    Uses a cheap model for 'free' plan and a stronger one for 'premium'.

    BUGFIX: Changed from non-existent 'responses' API to standard 'chat.completions' API.
    See: BUGFIXES.md #1
    """
    client = get_client()
    models = resolve_models()
    model = models.premium if plan == "premium" else models.free

    cfg = get_config()
    out_tokens = max_output_tokens or cfg.max_output_tokens

    # Use the Chat Completions API with JSON response format
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system
                    or "You are a senior technical SEO assistant. "
                       "Return concise, well-structured JSON only.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=temperature,
            max_tokens=out_tokens,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        raise AIError(f"OpenAI request failed: {e}")

    # Extract text from the response
    import json

    try:
        txt = resp.choices[0].message.content
        if not txt:
            raise AIError("OpenAI returned empty response")
        return json.loads(txt)
    except (IndexError, AttributeError, KeyError) as e:
        raise AIError(f"Could not parse OpenAI response structure: {e}")
    except json.JSONDecodeError as e:
        raise AIError(f"Model did not return valid JSON: {e}\nRaw: {txt[:400] if txt else 'None'}")
