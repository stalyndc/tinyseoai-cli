# 🧩 TinySEO AI — Claude / GLM Instructions

You are assisting in the development of **tinyseoai**, an intelligent SEO auditing CLI.

---

## 🎯 Objective

Help generate, refine, and document code inside the `tinyseoai/` package.
Follow the same design spec used by Codex (see AGENTS.md).

Your focus areas:

- **Claude:** write clear, well-commented Python functions and Typer CLI logic.
- **GLM:** improve rule-based SEO checks and AI prompt engineering.

---

## 🧠 Project Summary

- Language: **Python 3.11+**
- Runs locally as CLI; later connects to `api.tinyseoai.com`.
- Output: JSON, PDF, XLSX.
- Uses OpenAI API (4o-mini for free users, GPT-5 for premium).

---

## 🪜 Development Phases

1. **Local CLI (current phase)**  
   - Implement core crawl + audit functions.
   - Ensure output JSON and logs are correct.
2. **Reporting layer**  
   - Generate PDF and Excel reports from results.
3. **AI reasoning**  
   - Explain issues, summarize key findings.
4. **Backend integration (future)**  
   - Add license activation and plan validation.

---

## 🧰 Tools

- Typer / Rich for UX
- Async HTTPX crawler
- Pydantic models for structured data
- Jinja2 for report templates
- OpenAI client for text generation
- Pandas for data aggregation

---

Follow readable, modular, commented code.
Always test functions with small, known sites before scaling.
