# TinySEO AI - Multi-Agent System Documentation

## Overview

TinySEO AI now features a sophisticated **multi-agent AI system** powered by LangChain, enabling autonomous SEO analysis with specialized AI agents. This Phase 3 implementation transforms TinySEO AI from a rule-based audit tool into an intelligent, reasoning system that provides deeper insights and actionable recommendations.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Multi-Agent Coordinator                    │
│  (Orchestrates all agents, manages sessions, synthesizes)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼────────┐                  ┌─────────▼────────┐
│  Orchestrator  │                  │  Specialist      │
│     Agent      │─────────────────▶│    Agents        │
│  (Coordinator) │                  │                  │
└────────────────┘                  └──────┬───────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
            ┌───────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
            │ Technical SEO  │   │ Content Quality │   │  Performance   │
            │     Agent      │   │      Agent      │   │     Agent      │
            └────────────────┘   └─────────────────┘   └────────────────┘
                    │                      │                      │
            ┌───────▼────────┐   ┌────────▼────────┐
            │ Link Analysis  │   │  Fix Generator  │
            │     Agent      │   │      Agent      │
            └────────────────┘   └─────────────────┘
```

### Agent Roles

#### 1. **Orchestrator Agent**
- **Role**: Central coordinator
- **Responsibilities**:
  - Analyzes audit results and identifies priority areas
  - Creates task distribution plan for specialist agents
  - Monitors task execution
  - Synthesizes results from all agents
  - Generates comprehensive recommendations
- **Model**: GPT-4o (primary), GPT-4o-mini (fallback)

#### 2. **Technical SEO Agent**
- **Role**: Infrastructure specialist
- **Expertise**:
  - HTTPS and SSL certificate validation
  - Robots.txt configuration
  - XML sitemap analysis
  - Canonical tag implementation
  - Structured data (JSON-LD, Schema.org)
  - Security headers (CSP, HSTS, X-Frame-Options)
- **Model**: GPT-4o-mini (primary), GPT-4o (fallback)

#### 3. **Content Quality Agent**
- **Role**: On-page SEO specialist
- **Expertise**:
  - Title tag optimization
  - Meta description quality
  - Heading hierarchy (H1-H6)
  - Content readability scoring
  - Duplicate content detection
  - Image alt text optimization
- **Model**: GPT-4o-mini (primary), Claude 3.5 Sonnet (fallback)

#### 4. **Performance Agent**
- **Role**: Speed optimization specialist
- **Expertise**:
  - Image optimization opportunities
  - Render-blocking resources
  - Critical rendering path
  - Browser caching strategies
  - Core Web Vitals (LCP, FID, CLS)
- **Model**: GPT-4o-mini (primary), GPT-4o (fallback)

#### 5. **Link Analysis Agent**
- **Role**: Site architecture specialist
- **Expertise**:
  - Internal link graph analysis
  - Broken link detection (404s)
  - Orphan page identification
  - Anchor text optimization
  - Redirect chain analysis
  - Link equity distribution
- **Model**: GPT-4o-mini (primary), GPT-4o (fallback)

#### 6. **Fix Generator Agent**
- **Role**: Code implementation specialist
- **Expertise**:
  - Production-ready code generation
  - HTML/CSS/JavaScript snippets
  - .htaccess and nginx configuration
  - Robots.txt and sitemap.xml generation
  - Meta tag templates
  - Schema.org structured data markup
- **Model**: GPT-4o (primary for accuracy), GPT-4o-mini (fallback)

## Features

### 🧠 Chain-of-Thought Reasoning

Every agent uses explicit chain-of-thought reasoning to provide transparency in decision-making:

1. **Observation** - What data is being analyzed?
2. **Reflection** - What patterns or issues are present?
3. **Planning** - What actions should be taken?
4. **Action** - What is the decision?
5. **Verification** - Is the recommendation correct?

Each reasoning step includes:
- Confidence score (0.0 to 1.0)
- Supporting data/evidence
- Timestamp for performance tracking

### 🔄 Multi-Model Strategy

The system uses a fallback chain for resilience:
- **Primary Model**: GPT-4o-mini (fast, cost-effective)
- **Fallback Model 1**: GPT-4o (more capable)
- **Fallback Model 2**: Claude 3.5 Sonnet (alternative provider)

### 🎯 Smart Task Distribution

The Orchestrator Agent intelligently distributes work:
- Analyzes issue severity and type
- Assigns tasks to appropriate specialist agents
- Manages dependencies between tasks
- Executes specialist agents in parallel for speed

### 📊 Comprehensive Analysis

Multi-agent analysis provides:
- **Insights**: Key findings from each specialist
- **Recommendations**: Prioritized by impact/effort ratio
- **Confidence Scores**: Transparency in AI certainty
- **Code Fixes**: Production-ready implementation snippets

## Installation & Setup

### 1. Install Dependencies

The multi-agent system requires additional packages (already in `requirements.txt`):

```bash
pip install -r requirements.txt
```

Key dependencies:
- `langchain` - Agent framework
- `langchain-openai` - OpenAI integration
- `langchain-anthropic` - Claude integration
- `langchain-core` - Core abstractions

### 2. Configure API Keys

The easiest way is to use a `.env` file in your project root:

```bash
# Create or edit .env file
echo 'OPENAI_API_KEY=sk-proj-...' > .env
```

Your `.env` file should look like:
```
OPENAI_API_KEY=sk-proj-75mlh...M8kA
```

**Note**: The `.env` file is automatically loaded by TinySEO AI using `python-dotenv`.

Alternative - set as environment variable:
```bash
export OPENAI_API_KEY='sk-proj-...'
```

Optional - for Claude fallback (not required):
```bash
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env
```

### 3. Verify Configuration

Test that your API key is loaded correctly:

```bash
python test_env_config.py
```

Expected output:
```
✅ OpenAI API Key loaded: sk-proj-75...M8kA
   Length: 164 characters
ℹ️  Anthropic API Key not set (optional, not used)

📊 Multi-Agent Settings:
   Enabled: True
   Chain of Thought: True
   Max Concurrent Agents: 3
   Plan: free

✅ Configuration is ready for AI-powered audits!
```

## Usage

### Basic AI-Powered Audit

Run a multi-agent analysis on any website:

```bash
tinyseoai audit-ai https://example.com
```

This will:
1. Run comprehensive SEO audit (Phase 2 checks)
2. Deploy all 6 AI agents for analysis
3. Generate code fixes
4. Provide prioritized recommendations

### Advanced Options

**Limit pages scanned:**
```bash
tinyseoai audit-ai https://example.com --pages 20
```

**Skip code fix generation:**
```bash
tinyseoai audit-ai https://example.com --no-fixes
```

**Custom output directory:**
```bash
tinyseoai audit-ai https://example.com --out ./my-reports
```

### Output Files

The command creates two files:

1. **`comprehensive_summary.json`** - Full audit results
2. **`agent_analysis.json`** - Multi-agent AI analysis

Structure of `agent_analysis.json`:

```json
{
  "session_id": "session_1234567890.123",
  "site_url": "https://example.com",
  "total_tasks": 5,
  "completed_tasks": 5,
  "total_tokens": 12500,
  "average_confidence": 0.89,

  "orchestration": {
    "insights": ["Critical: 15 high-severity issues require immediate attention"],
    "recommendations": [...],
    "confidence": 0.95
  },

  "specialist_analysis": {
    "technical_seo": {
      "success": true,
      "insights": ["Security Alert: 3 HTTPS/SSL issues detected"],
      "recommendations": [...],
      "confidence": 0.91,
      "execution_time_ms": 2340
    },
    "content_quality": {...},
    "performance": {...},
    "link_analysis": {...},
    "fix_generator": {...}
  },

  "top_recommendations": [
    {
      "title": "Enable HTTPS Site-Wide",
      "description": "Fix 3 HTTPS/SSL issues...",
      "priority": "critical",
      "impact": 9.0,
      "effort": 7.0,
      "category": "security"
    },
    ...
  ],

  "key_insights": [
    "Critical: Site health score is 45/100 - immediate action required",
    "Security concerns detected: 3 issues affecting site trustworthiness",
    ...
  ],

  "chain_of_thought_summary": [
    {
      "agent": "technical_seo",
      "goal": "Analyze technical SEO issues...",
      "steps": 5,
      "confidence": 0.91,
      "reasoning_time_ms": 1200
    },
    ...
  ]
}
```

## CLI Output Example

```
═══════════════════════════════════════════════════════════
 🤖 TinySEO AI — Multi-Agent Analysis  (FREE mode)
═══════════════════════════════════════════════════════════
Initializing AI agents...

📊 Phase 1: Running comprehensive SEO audit...
✅ Audit complete: 33 issues found

🤖 Phase 2: Deploying specialist AI agents...

✅ Multi-agent analysis complete!

        🎯 Analysis Summary — https://example.com
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric          ┃ Value                              ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Pages Scanned   │ 5                                  │
│ Issues Found    │ 33                                 │
│ Health Score    │ 45/100                             │
│ Agents Deployed │ 5                                  │
│ Total Tokens    │ 12,450                             │
│ Avg Confidence  │ 89.2%                              │
└─────────────────┴────────────────────────────────────┘

💡 Key Insights:
  1. Critical: Site health score is 45/100 - immediate action required
  2. Security Alert: 3 HTTPS/SSL issues detected - may affect rankings
  3. Content Alert: 8 title tag issues - titles are critical for rankings
  4. Found 5 broken links - fix these to improve user experience
  5. Performance Alert: 7 image optimization opportunities

        🔧 Top Priority Recommendations
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┓
┃ Priority┃ Recommendation                ┃ Impact┃ Effort┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━┩
│ 4.5     │ Optimize Title Tags           │ 8.5   │ 3.0   │
│ 2.7     │ Fix Broken Links              │ 7.0   │ 3.0   │
│ 2.3     │ Create robots.txt File        │ 7.0   │ 2.0   │
│ 1.9     │ Optimize Images               │ 7.5   │ 4.0   │
│ 1.6     │ Defer Render-Blocking         │ 8.0   │ 5.0   │
└─────────┴───────────────────────────────┴───────┴───────┘

🧠 Agent Reasoning Summary:
  • orchestrator: 5 reasoning steps (95.0% confidence, 1834ms)
  • technical_seo: 5 reasoning steps (91.2% confidence, 2340ms)
  • content_quality: 5 reasoning steps (88.4% confidence, 2156ms)
  • performance: 5 reasoning steps (87.9% confidence, 2089ms)
  • link_analysis: 5 reasoning steps (89.6% confidence, 2234ms)

📁 Results saved:
  • Audit: reports/example.com/comprehensive_summary.json
  • AI Analysis: reports/example.com/agent_analysis.json

📊 Agent Performance:
  • orchestrator: 1 tasks, avg 1834ms
  • technical_seo: 1 tasks, avg 2340ms
  • content_quality: 1 tasks, avg 2156ms
  • performance: 1 tasks, avg 2089ms
  • link_analysis: 1 tasks, avg 2234ms
```

## Cost Estimation

Typical costs per audit (using GPT-4o-mini):

| Pages Scanned | Approx. Tokens | Est. Cost (USD) |
|---------------|----------------|-----------------|
| 5 pages       | ~12,000        | $0.02 - $0.05   |
| 10 pages      | ~18,000        | $0.03 - $0.08   |
| 20 pages      | ~25,000        | $0.04 - $0.12   |
| 50 pages      | ~40,000        | $0.06 - $0.20   |

*Costs are approximate and depend on issue count and complexity.*

## Advanced Configuration

### Customize Agent Behavior

Edit `~/.config/tinyseoai/config.json`:

```json
{
  "enable_multi_agent": true,
  "enable_chain_of_thought": true,
  "max_concurrent_agents": 5,
  "openai_api_key": "sk-...",
  "anthropic_api_key": "sk-ant-..."
}
```

Options:
- `enable_multi_agent` - Enable/disable AI agents (default: true)
- `enable_chain_of_thought` - Enable explicit reasoning (default: true)
- `max_concurrent_agents` - Max parallel agents (default: 3)

### Programmatic Usage

```python
import asyncio
from tinyseoai.audit.engine_v2 import comprehensive_audit
from tinyseoai.agents.coordinator import MultiAgentCoordinator

# Step 1: Run comprehensive audit
result = asyncio.run(comprehensive_audit("https://example.com", max_pages=10))

# Step 2: Analyze with AI agents
coordinator = MultiAgentCoordinator(openai_api_key="sk-...")
analysis = asyncio.run(
    coordinator.analyze_with_agents(result, enable_fix_generation=True)
)

# Step 3: Access results
for insight in analysis["key_insights"]:
    print(f"💡 {insight}")

for rec in analysis["top_recommendations"][:5]:
    print(f"🔧 {rec['title']}: {rec['description']}")
```

## Testing

### Run Unit Tests

```bash
pytest tests/unit/test_agent_models.py -v
```

### Run Integration Tests

```bash
# Requires valid API key
export OPENAI_API_KEY='sk-...'
pytest tests/integration/test_multi_agent.py -v -m ai
```

### Run All Agent Tests

```bash
pytest tests/ -v -m "unit or ai"
```

## Troubleshooting

### API Key Not Found

**Error**: `OPENAI_API_KEY not found`

**Solution**:
```bash
export OPENAI_API_KEY='your-key-here'
# Or add to your ~/.bashrc or ~/.zshrc
```

### Rate Limit Exceeded

**Error**: `Rate limit exceeded`

**Solution**:
- Reduce `max_concurrent_agents` in config
- Use `--pages` flag to limit scan size
- Wait and retry (OpenAI has per-minute limits)

### Agent Task Failed

**Error**: `Agent task failed: <error>`

**Solution**:
- Check your API key is valid
- Verify you have sufficient API credits
- Review the full error in the terminal output
- The base audit results are still saved successfully

### Low Confidence Scores

**Issue**: Agents returning confidence < 70%

**Solution**:
- This is normal for complex issues
- Review the chain-of-thought reasoning
- Consider the agent's insights carefully
- Cross-reference with manual inspection

## Comparison: Basic vs Full vs AI Audit

| Feature | `audit` | `audit-full` | `audit-ai` |
|---------|---------|--------------|------------|
| Speed | ⚡ Fastest | 🚀 Fast | 🤖 Moderate |
| Issues Detected | 7 types | 50+ types | 50+ types |
| Health Score | ❌ No | ✅ Yes | ✅ Yes |
| AI Analysis | ❌ No | ❌ No | ✅ Yes |
| Chain of Thought | ❌ No | ❌ No | ✅ Yes |
| Code Fixes | ❌ No | ❌ No | ✅ Yes |
| Cost | Free | Free | ~$0.02-0.20 |
| Best For | Quick checks | Full audit | Deep analysis |

## Roadmap

### Completed ✅
- [x] Multi-agent architecture with LangChain
- [x] 6 specialist AI agents
- [x] Chain-of-thought reasoning framework
- [x] Multi-model fallback strategy
- [x] Parallel agent execution
- [x] CLI integration (`audit-ai`)
- [x] Comprehensive test coverage

### Planned 🚧
- [ ] **Phase 4**: Memory & Learning System
  - SQLAlchemy + ChromaDB for knowledge storage
  - Learning from past audits
  - Personalized recommendations

- [ ] **Phase 5**: Autonomous Actions
  - Auto-fix generation and application
  - Git integration for pull requests
  - Continuous monitoring

- [ ] **Phase 6**: Enhanced UX
  - Interactive HTML reports with agent insights
  - Real-time progress streaming
  - Agent conversation visualization

## Support & Contributing

- **Issues**: https://github.com/your-org/tinyseoai-cli/issues
- **Documentation**: https://docs.tinyseoai.com
- **Discussions**: https://github.com/your-org/tinyseoai-cli/discussions

## License

TinySEO AI is licensed under the MIT License. See LICENSE file for details.

---

**Built with ❤️ using LangChain, OpenAI GPT-4o, and Claude 3.5 Sonnet**
