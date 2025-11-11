from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_config_dir
from pydantic import BaseModel, Field

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
    cfg_dir = Path(user_config_dir(APP_NAME))
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / "config.json"


def get_config() -> AppConfig:
    """
    Load application configuration from disk or create default.

    BUGFIX: Improved exception handling and logging.
    See: BUGFIXES.md #4
    """
    p = _cfg_path()
    if p.exists():
        try:
            return AppConfig(**json.loads(p.read_text()))
        except (json.JSONDecodeError, ValueError) as e:
            # Config file is corrupted, log warning and recreate
            import sys
            print(f"Warning: Config file corrupted ({e}), recreating with defaults", file=sys.stderr)

    # Create new config file
    cfg = AppConfig()
    try:
        p.write_text(cfg.model_dump_json(indent=2))
    except OSError as e:
        # Can't write config, but continue with default in-memory config
        import sys
        print(f"Warning: Cannot write config file ({e}), using defaults", file=sys.stderr)

    return cfg


def save_config(cfg: AppConfig) -> None:
    """
    Save configuration to disk atomically.

    BUGFIX: Use atomic write to prevent corruption from concurrent access.
    See: BUGFIXES.md #5
    """
    import os
    import tempfile

    p = _cfg_path()
    content = cfg.model_dump_json(indent=2)

    # Write to temporary file first
    fd, temp_path = tempfile.mkstemp(
        dir=p.parent,
        prefix=".config_",
        suffix=".tmp"
    )
    try:
        os.write(fd, content.encode('utf-8'))
        os.close(fd)
        # Atomic rename (POSIX guarantees atomicity)
        os.replace(temp_path, p)
    except Exception:
        # Clean up temp file on error
        try:
            os.close(fd)
        except Exception:
            pass
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        raise
