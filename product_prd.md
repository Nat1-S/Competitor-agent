# Product Requirements Document (PRD)

## Competitor Strategic Agent

**Version:** 1.0  
**Status:** Engineering Hand-off Ready  
**Last Updated:** February 2026

---

## 1. Product Name

**Competitor Strategic Agent** (מנתח מוצרים אסטרטגי)

A Senior Product Manager–powered agent that automates competitor research by scraping product URLs, performing strategic and technical UX analysis via Claude, and delivering structured reports in Hebrew.

---

## 2. The Problem

Manual competitor research is time-consuming and often lacks deep strategic or technical UX insights. Teams spend hours:

- Copying content from competitor sites
- Manually comparing value propositions and business models
- Hunting for UX friction points and conversion blockers
- Struggling to produce actionable, structured analysis

**Pain points:**
- Inconsistent analysis quality and depth
- No standardized framework for strategic vs. technical insights
- Language barriers (most tools assume English)
- Limited technical QA audit (accessibility, mobile-readability, conversion blockers)

---

## 3. Target Personas

### 3.1 Product Managers
- **Needs:** Rapid market positioning, value proposition mapping, and competitive differentiation
- **Use case:** Pre–go-to-market research, positioning decks, strategy documents
- **Key outcomes:** Product Essence, Strategy, Feature Inventory, Comparison Tables

### 3.2 UX / QA Leads
- **Needs:** Concrete technical UI flaws, conversion blockers, accessibility and mobile-readability issues
- **Use case:** QA backlogs, UX audit reports, sprint planning
- **Key outcomes:** QA Friction Points, Suggestions for Improvement, Strengths & Weaknesses

---

## 4. User Experience (UX)

### 4.1 End-to-End Flow (4 Steps)

| Step | Name | Description |
|------|------|-------------|
| 1 | **URL Input** | User enters a main product URL and optionally adds competitor URLs. Dynamic competitor rows with add/remove (X) controls. |
| 2 | **Firecrawl Scraping** | URLs are scraped via Firecrawl API into Markdown. Failed scrapes are reported; analysis continues with successful URLs only. |
| 3 | **Claude Analysis** | Scraped Markdown (truncated to 15k chars) is sent to Anthropic Claude with a Senior PM system prompt. Output is structured Markdown in Hebrew. |
| 4 | **Streamlit Reporting** | Report is rendered in a dark-themed, RTL Hebrew UI. Sections include Product Essence, Strategy, Feature Inventory, Strengths & Weaknesses, QA Friction Points, Suggestions, and a comparison table when multiple products are provided. |

### 4.2 Access Control
- Password-only login (single shared password)
- Session-based authentication; logout button in the top-left (RTL layout)

### 4.3 Layout & Localization
- RTL (right-to-left) layout for Hebrew
- Dark theme aligned with Streamlit defaults
- Responsive layout for wide screens

---

## 5. Proposed Solution (Features)

### 5.1 Automated Markdown Scraping via Firecrawl
- Converts web pages to clean Markdown for LLM consumption
- Handles multiple URLs in sequence
- Returns per-URL success/failure with error messages
- Integrates via `firecrawl-py` (Firecrawl SDK)

### 5.2 Strategic Analysis
- **Product Essence:** Value proposition, problem solved, core offering
- **Strategy:** Target audience, positioning, business model
- **Feature Inventory:** Key capabilities and product scope
- **Comparison Table:** Side-by-side comparison when multiple products are provided

### 5.3 Technical QA & UX Audit
- **QA Friction Points:** Usability gaps, conversion blockers, technical friction
- **Strengths & Weaknesses:** UX and value-prop analysis
- **Suggestions for Improvement:** Concrete, actionable recommendations
- Implicit coverage of accessibility, mobile-readability, and conversion-critical elements via the PM system prompt

### 5.4 Output
- Hebrew Markdown report
- Structured sections with headers for easy scanning
- Optional structured output (e.g., Pydantic `StrategicProductReport`) for expandable UI sections

---

## 6. Technical Mapping

### 6.1 Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────────┐
│  URL Input      │────▶│  Firecrawl   │────▶│   Claude    │────▶│  Streamlit      │
│  (Streamlit)    │     │  Scraper     │     │  Analyzer   │     │  Report UI      │
└─────────────────┘     └──────────────┘     └─────────────┘     └─────────────────┘
```

### 6.2 Frontend
- **Framework:** Streamlit
- **Deployment target:** Streamlit Cloud
- **Entry point:** `app.py` (run via `streamlit run app.py`)

### 6.3 Core Logic

| File | Responsibility |
|------|----------------|
| `app.py` | Streamlit UI, login, URL input, competitor rows, report display, orchestration |
| `analyzer.py` | Claude API calls, system prompt, markdown cleaning, retry logic, error handling |
| `scraper.py` | Firecrawl integration, `scrape_urls()`, result object (`url`, `success`, `markdown`, `error`) |
| `schema.py` | Pydantic models (ProductEssence, Strategy, StrengthsWeaknesses, QAOptimization, StrategicProductReport) |

### 6.4 LLM
- **Provider:** Anthropic
- **Model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`)
- **Override:** `ANTHROPIC_MODEL` env var
- **API Key:** `ANTHROPIC_API_KEY` (from `.env`)

### 6.5 Integrations
- **Firecrawl API:** Web-to-Markdown conversion
- **API Key:** `FIRECRAWL_API_KEY` (from `.env`)

### 6.6 Environment & Security
- **Config:** `.env` (excluded from version control via `.gitignore`)
- **Required vars:** `FIRECRAWL_API_KEY`, `ANTHROPIC_API_KEY`
- **Optional:** `APP_PASSWORD` (login), `ANTHROPIC_MODEL` (model override)

---

## 7. File Structure (Engineering Reference)

```
competitor agent/
├── app.py              # Streamlit UI entry point, login, report display
├── analyzer.py         # Claude integration, run_analysis(), markdown cleaning
├── scraper.py          # Firecrawl integration, scrape_urls()
├── schema.py           # Pydantic models for structured report
├── requirements.txt    # Dependencies (firecrawl-py, anthropic, streamlit, etc.)
├── .env                # API keys (not committed)
├── .gitignore          # Excludes .env, venv, __pycache__
├── pyrightconfig.json  # Type checker config
├── README.md           # Setup and run instructions
└── product_prd.md      # This PRD
```

---

## 8. Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | UI |
| `anthropic` | Claude API |
| `firecrawl-py` | Web scraping to Markdown |
| `python-dotenv` | Load `.env` |
| `pydantic` | Data validation and structured output |
| `httpx` | HTTP client (optional, for analyzer timeouts) |

---

## 9. Success Criteria

- [ ] User can enter product + competitor URLs and receive a Hebrew strategic report within minutes
- [ ] Report includes all six core sections (Product Essence, Strategy, Feature Inventory, Strengths & Weaknesses, QA Friction Points, Suggestions)
- [ ] Comparison table appears when multiple products are provided
- [ ] Login protects access; logout works as expected
- [ ] RTL layout and Hebrew output are correct and readable

---

## 10. Future Enhancements (Out of Scope for v1)

- Structured output (JSON) instead of free-form Markdown
- Multi-language output (e.g., English toggle)
- Export to PDF / Notion / Google Docs
- Crawl multiple pages per URL (Firecrawl crawl mode)
