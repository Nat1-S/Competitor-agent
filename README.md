# Strategic Product Analyst | מנתח מוצרים אסטרטגי

A Senior Product Manager Agent powered by Claude that scrapes product URLs, performs strategic and UX analysis, and produces detailed reports in Hebrew with Google Docs export.

## Features

- 🔍 **URL Scraping** – Scrapes product pages via Firecrawl API
- 🤖 **AI Analysis** – Claude-powered strategic PM analysis
- 📊 **Hebrew Reports** – RTL formatted reports in Hebrew
- 📄 **Google Docs Export** – One-click export to shareable Google Docs
- 🔐 **Password Protection** – Simple login authentication
- 🌐 **Cloud Ready** – Deployable to Streamlit Cloud

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file:

```env
FIRECRAWL_API_KEY=fc-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
APP_PASSWORD=YourPassword
```

### 3. Run the app

```bash
streamlit run app.py
```

## Google Docs Export (Optional)

To enable the "הפץ ל-Docs" feature:

### Local Development

1. Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Docs API and Google Drive API
3. Download credentials as `oauth_credentials.json`
4. On first export, a browser will open for authentication
5. Token is saved to `token.json` for future use

### Streamlit Cloud

Add to Streamlit Secrets:

```toml
GOOGLE_TOKEN_JSON = '{"token":"...","refresh_token":"...","client_id":"...","client_secret":"..."}'
```

## Project Structure

```
competitor agent/
├── app.py              # Streamlit UI, login, report display
├── analyzer.py         # Claude API integration, PM analysis
├── scraper.py          # Firecrawl web scraping
├── schema.py           # Pydantic models
├── google_exporter.py  # Google Docs export
├── requirements.txt    # Dependencies
├── product_prd.md      # Product Requirements Document
└── README.md           # This file
```

## Report Sections

The strategic report includes:

| Section | Description |
|---------|-------------|
| **מהות המוצר** | Product essence, value proposition, problem solved |
| **אסטרטגיה** | Target audience, positioning, business model |
| **מפת יכולות** | Feature inventory and capabilities |
| **חוזקות וחולשות** | Strengths & weaknesses analysis |
| **נקודות חיכוך QA** | UX friction points, conversion blockers |
| **הצעות לשיפור** | Actionable improvement suggestions |
| **טבלת השוואה** | Comparison table (when multiple URLs) |

## Deployment to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Add secrets in Settings:

```toml
FIRECRAWL_API_KEY = "fc-..."
ANTHROPIC_API_KEY = "sk-ant-..."
APP_PASSWORD = "YourPassword"
GOOGLE_TOKEN_JSON = '{"token":"...", ...}'
```

5. Deploy!

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FIRECRAWL_API_KEY` | Yes | Firecrawl API key for scraping |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for Claude |
| `APP_PASSWORD` | No | Login password (default: `Snati#3155`) |
| `ANTHROPIC_MODEL` | No | Override model (default: `claude-sonnet-4-6`) |
| `GOOGLE_TOKEN_JSON` | No | Google OAuth token for Docs export |

## Error Handling

- Failed scrapes are reported per URL; analysis continues with successful URLs
- Google Docs export failures show a warning but preserve the report in UI
- API errors display user-friendly Hebrew messages

## License

Private project.
