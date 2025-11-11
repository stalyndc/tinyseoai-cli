#!/usr/bin/env python3
"""
Quick test to verify .env loading and API key configuration.
"""

from tinyseoai.config import get_config

def test_env_loading():
    """Test that .env file is loaded correctly."""
    print("=" * 60)
    print("Testing .env Configuration")
    print("=" * 60)

    cfg = get_config()

    # Test OpenAI API key
    api_key = cfg.openai_api_key

    if api_key:
        # Mask the key for security
        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
        print(f"✅ OpenAI API Key loaded: {masked_key}")
        print(f"   Length: {len(api_key)} characters")
    else:
        print("❌ OpenAI API Key NOT found")
        print("   Make sure .env file exists with OPENAI_API_KEY")

    # Test Anthropic (optional)
    anthropic_key = cfg.anthropic_api_key
    if anthropic_key:
        masked = f"{anthropic_key[:10]}...{anthropic_key[-4:]}"
        print(f"✅ Anthropic API Key loaded: {masked} (optional)")
    else:
        print("ℹ️  Anthropic API Key not set (optional, not used)")

    # Show multi-agent settings
    print(f"\n📊 Multi-Agent Settings:")
    print(f"   Enabled: {cfg.enable_multi_agent}")
    print(f"   Chain of Thought: {cfg.enable_chain_of_thought}")
    print(f"   Max Concurrent Agents: {cfg.max_concurrent_agents}")
    print(f"   Plan: {cfg.plan}")

    print("\n" + "=" * 60)

    if api_key:
        print("✅ Configuration is ready for AI-powered audits!")
        print("   Run: tinyseoai audit-ai https://example.com")
    else:
        print("❌ Configuration incomplete")
        print("   Add OPENAI_API_KEY to .env file")

    print("=" * 60)

    return bool(api_key)


if __name__ == "__main__":
    success = test_env_loading()
    exit(0 if success else 1)
