# TinySEO AI - Quick Start Guide

Get started with AI-powered SEO audits in 3 simple steps!

## 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

## 2️⃣ Configure API Key

Your `.env` file already contains your OpenAI API key! 🎉

Verify it's working:
```bash
python test_env_config.py
```

Expected output:
```
✅ OpenAI API Key loaded: sk-proj-75...M8kA
✅ Configuration is ready for AI-powered audits!
```

## 3️⃣ Run Your First AI Audit

```bash
# Basic audit (fast, no AI)
tinyseoai audit https://example.com

# Comprehensive audit (all checks, no AI)
tinyseoai audit-full https://example.com

# 🤖 AI-powered audit (recommended!)
tinyseoai audit-ai https://example.com
```

## 🤖 AI-Powered Audit Features

The `audit-ai` command deploys 6 specialist AI agents:

1. **Orchestrator** - Coordinates all agents
2. **Technical SEO** - HTTPS, security, robots.txt
3. **Content Quality** - Titles, meta tags, headings
4. **Performance** - Speed optimization, images
5. **Link Analysis** - Broken links, site architecture
6. **Fix Generator** - Production-ready code fixes

### What You Get:

✅ Chain-of-thought reasoning (see how AI makes decisions)
✅ Prioritized recommendations (impact vs effort)
✅ Production-ready code fixes
✅ Confidence scores for each insight
✅ Comprehensive analysis from multiple specialists

### Output Files:

```
reports/example.com/
├── comprehensive_summary.json  # Full SEO audit results
└── agent_analysis.json         # AI insights & recommendations
```

## 📊 Sample Output

```
═══════════════════════════════════════════════════════════
 🤖 TinySEO AI — Multi-Agent Analysis  (FREE mode)
═══════════════════════════════════════════════════════════

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
  2. Security Alert: 3 HTTPS/SSL issues detected
  3. Content Alert: 8 title tag issues found
  4. Found 5 broken links requiring fixes
  5. Performance: 7 image optimization opportunities

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
```

## 🎯 Command Comparison

| Feature | `audit` | `audit-full` | `audit-ai` |
|---------|---------|--------------|------------|
| Speed | ⚡ 10s | 🚀 30s | 🤖 60s |
| Issues Found | 7 types | 50+ types | 50+ types |
| Health Score | ❌ | ✅ | ✅ |
| AI Analysis | ❌ | ❌ | ✅ |
| Code Fixes | ❌ | ❌ | ✅ |
| Cost | Free | Free | ~$0.02-0.20 |
| **Best For** | Quick check | Full audit | Deep insights |

## 💰 Cost Estimate

Using GPT-4o-mini (default):
- **5 pages**: $0.02 - $0.05
- **10 pages**: $0.03 - $0.08
- **20 pages**: $0.04 - $0.12
- **50 pages**: $0.06 - $0.20

Very affordable for comprehensive AI analysis!

## 📖 More Documentation

- **Full Agent Documentation**: See [AGENTS_README.md](./AGENTS_README.md)
- **Project README**: See [README.md](./README.md)

## 🛠️ Troubleshooting

### API Key Not Loading?

```bash
# Verify .env file exists
ls -la .env

# Test configuration
python test_env_config.py

# Check .env content (be careful not to share!)
cat .env
```

### Still Having Issues?

```bash
# Check Python version (requires 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Run basic audit first (no API key needed)
tinyseoai audit https://example.com
```

## 🎉 You're Ready!

Start auditing with AI:

```bash
tinyseoai audit-ai https://your-website.com
```

Enjoy intelligent, autonomous SEO analysis! 🚀
