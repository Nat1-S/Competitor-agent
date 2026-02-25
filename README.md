# Strategic Product Analyst | מנתח מוצרים אסטרטגי

A Senior Product Manager Agent that scrapes product URLs, analyzes them with a strategic PM lens, and produces a detailed mapping and comparison report in Hebrew.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. API Keys (in `.env` via python-dotenv)

- **Firecrawl**: `FIRECRAWL_API_KEY` (get from [firecrawl.dev](https://firecrawl.dev))
- **Gemini**: `GOOGLE_API_KEY` or `GEMINI_API_KEY` (get from [aistudio.google.com](https://aistudio.google.com))

### 3. Run the app

```bash
streamlit run app.py
```

## Project Structure

```
competitor agent/
├── app.py          # Streamlit UI entry point
├── analyzer.py     # PM Agent LLM logic (LiteLLM)
├── schema.py       # Pydantic models for structured output
├── scraper.py      # Firecrawl integration
├── requirements.txt
└── README.md
```

## Features

- **Product URL input** – Main product URL field
- **Add Competitor** – Dynamic competitor URL fields for comparison
- **Run Analysis** – Triggers scrape → PM Agent analysis
- **Strategic Product Report** – Hebrew output with:
  - Product Essence (what it does, problem solved)
  - Strategy (target audience, positioning, business model)
  - Feature Inventory
  - Strengths & Weaknesses
  - QA & Optimization (friction points, suggestions)
  - Side-by-side comparison table (when multiple URLs)

## Model Configuration

Default: `gemini/gemini-1.5-pro` via LiteLLM.

Override via env: `PM_AGENT_MODEL="gemini/gemini-1.5-pro"`

## Firecrawl (Complex URLs)

Scraping is configured for complex sites (e.g., Amazon):
- `wait_for`: 2s for JS-heavy pages
- `timeout`: 45s per page
- `only_main_content`: true to focus on product content

## Error Handling

- Failed scrapes (blocked, rate-limited, invalid URLs) are reported per URL
- Analysis continues with successfully scraped URLs only
- LLM errors surface a message in the report
