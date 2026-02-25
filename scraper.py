"""
Firecrawl-based URL scraper for the Senior PM Agent.

Scrapes URLs and returns markdown content for analysis.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv(Path(__file__).resolve().parent / ".env")


def scrape_urls(urls: list[str]) -> list:
    """
    Scrape multiple URLs using Firecrawl and return results.

    Args:
        urls: List of URLs to scrape.

    Returns:
        List of objects with: url, success, markdown, error.

    Raises:
        ValueError: If FIRECRAWL_API_KEY is missing or urls is empty.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY is not set. Add it to your .env file.")

    if not urls:
        raise ValueError("No URLs provided.")

    client = Firecrawl(api_key=api_key)
    results = []

    for url in urls:
        url = (url or "").strip()
        if not url:
            continue

        try:
            doc = client.scrape(url)
            markdown = getattr(doc, "markdown", None) or ""
            results.append(
                _ScrapeResult(url=url, success=True, markdown=markdown, error=None)
            )
        except Exception as e:
            results.append(
                _ScrapeResult(url=url, success=False, markdown=None, error=str(e))
            )

    return results


class _ScrapeResult:
    """Lightweight result object with url, success, markdown, error."""

    __slots__ = ("url", "success", "markdown", "error")

    def __init__(
        self,
        url: str,
        success: bool,
        markdown: str | None,
        error: str | None,
    ) -> None:
        self.url = url
        self.success = success
        self.markdown = markdown
        self.error = error
