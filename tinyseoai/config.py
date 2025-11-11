from __future__ import annotations
import json
import os
from pathlib import Path
from pydantic import BaseModel, Field
from platformdirs import user_config_dir
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

APP_NAME = "tinyseoai"


class BrandConfig(BaseModel):
    name: str = "TinySEO AI"
    accent_hex: str = "#95E1D3"        # default teal from your palette
    show_bot_logo: bool = True          # toggle inline SVG logo in PDF


class AppConfig(BaseModel):
    api_base: str = "https://api.tinyseoai.com"
    plan: str = "free"  # free | premium
    openai_model_free: str = "gpt-4o-mini"
    openai_model_premium: str = "gpt-5"
    max_output_tokens: int = 800
    brand: BrandConfig = Field(default_factory=BrandConfig)

    # AI Agent API Keys (loaded from .env file or environment variables)
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment (optional)."""
        return os.getenv("ANTHROPIC_API_KEY", "")

    # Multi-agent settings
    enable_multi_agent: bool = True
    enable_chain_of_thought: bool = True
    max_concurrent_agents: int = 3


def _cfg_path() -> Path:
    from platformdirs import user_config_dir
    cfg_dir = Path(user_config_dir(APP_NAME))
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "config.json"


def get_config() -> AppConfig:
    p = _cfg_path()
    if p.exists():
        try:
            return AppConfig(**json.loads(p.read_text()))
        except Exception:
            pass
    cfg = AppConfig()
    p.write_text(cfg.model_dump_json(indent=2))
    return cfg


def save_config(cfg: AppConfig) -> None:
    _cfg_path().write_text(cfg.model_dump_json(indent=2))
