"""
Senior Product Manager Agent - LLM analysis via Anthropic Claude.

Persona: Senior PM (10 years experience). Focus: Product Strategy, Value Proposition, QA friction points.
Output: Detailed structured Markdown in HEBREW.
Requires ANTHROPIC_API_KEY in .env.
"""

from dotenv import load_dotenv
from pathlib import Path

# Load .env BEFORE any environment variables are accessed
load_dotenv(Path(__file__).resolve().parent / ".env")

import os
import re
import time
import socket

# DNS workaround: Some networks block connections when resolving via domain
# but allow direct IP connections. We cache the IP on first successful resolution.
_ANTHROPIC_IP_CACHE = None
_original_getaddrinfo = socket.getaddrinfo

def _patched_getaddrinfo(host, port, *args, **kwargs):
    global _ANTHROPIC_IP_CACHE
    if host == 'api.anthropic.com':
        if _ANTHROPIC_IP_CACHE is None:
            # Resolve once and cache
            results = _original_getaddrinfo(host, port, socket.AF_INET, *args[1:], **kwargs)
            if results:
                _ANTHROPIC_IP_CACHE = results[0][4][0]
        if _ANTHROPIC_IP_CACHE:
            # Return cached IP to force connection via IP
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (_ANTHROPIC_IP_CACHE, port))]
    return _original_getaddrinfo(host, port, *args, **kwargs)

socket.getaddrinfo = _patched_getaddrinfo

MAX_CHARS = 15_000  # Truncate scraped Markdown for depth and efficiency

NAV_PHRASES = (
    "home", "about", "contact", "privacy", "terms", "cookie", "sign in", "log in",
    "menu", "search", "cart", "shipping", "returns", "faq", "help", "support",
    "subscribe", "newsletter", "facebook", "twitter", "instagram", "linkedin",
    "©", "all rights reserved", "terms of service", "privacy policy", "cookies",
    "מדיניות פרטיות", "תנאי שימוש", "צור קשר", "דף הבית", "אודות",
)

SYSTEM_PROMPT = """You are a Senior Product Manager with 10 years of experience. Focus on:
- Product Strategy and Go-to-Market
- Value Proposition and Differentiation
- QA Friction Points and Usability Issues

Analyze the provided product website data and produce a **detailed, structured Markdown report in HEBREW**. The response MUST be in Hebrew.

Include these sections (use ## headers in Hebrew):
1. **מהות המוצר** (Product Essence) - Value proposition, problem solved
2. **אסטרטגיה** (Strategy) - Target audience, positioning, business model
3. **מפת יכולות** (Feature Inventory) - Key capabilities
4. **נקודות חוזק וחולשה** (Strengths & Weaknesses) - UX and value-prop analysis
5. **נקודות חיכוך QA** (QA Friction Points) - Usability gaps, conversion blockers, friction
6. **הצעות לשיפור** (Suggestions for Improvement) - Concrete recommendations

If multiple products are provided, add a comparison table (טבלת השוואה).

Output ONLY the Markdown report in HEBREW. No preamble."""


def _clean_scraped_markdown(text: str) -> str:
    """Remove code, CSS, nav menus; keep content useful for PM analysis."""
    if not text or not text.strip():
        return ""

    text = re.sub(r"```[\s\S]*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)

    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        lower = s.lower()
        if any(nav in lower for nav in NAV_PHRASES) and len(s) < 80:
            continue
        if s.count("{") + s.count("}") + s.count(";") > 3:
            continue
        if s.startswith("```") or s.startswith("#include") or "function(" in lower:
            continue
        if re.match(r"^https?://\S+$", s):
            continue
        if len(s) > 300:
            s = s[:300] + "..."
        if len(s) < 20 and s.replace("-", "").replace("|", "").replace("/", "").strip().replace(" ", "").isalpha():
            continue
        lines.append(s)

    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return out[:MAX_CHARS]


def run_analysis(scraped_data: str) -> str:
    """
    Run PM analysis via Anthropic Claude.
    Uses ANTHROPIC_API_KEY from .env only.
    Returns Markdown report in Hebrew, or error message string.
    """
    try:
        import anthropic
    except ImportError:
        return "שגיאה: anthropic לא מותקן. הרץ: pip install anthropic"

    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key or not str(key).strip():
        return "שגיאה: ANTHROPIC_API_KEY לא נמצא בקובץ .env"

    clean_text = _clean_scraped_markdown(str(scraped_data or ""))
    if not clean_text.strip():
        return "שגיאה: לא נמצא תוכן לניתוח לאחר הניקוי."

    user_content = f"Product website data to analyze:\n\n---\n\n{clean_text}"

    try:
        import httpx
        # Force HTTP/1.1 - HTTP/2 is blocked by some networks
        http_client = httpx.Client(
            timeout=120.0,
            http1=True,
            http2=False,
            trust_env=False
        )
        client = anthropic.Anthropic(
            api_key=key,
            base_url="https://api.anthropic.com",
            http_client=http_client,
        )
    except ImportError:
        client = anthropic.Anthropic(
            api_key=key,
            base_url="https://api.anthropic.com",
            timeout=120.0,
        )

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6").strip()
    if not model:
        model = "claude-sonnet-4-6"

    def _call():
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        if response.content:
            for block in response.content:
                text = getattr(block, "text", None)
                if text:
                    return text
        return "שגיאה: לא התקבלה תשובה מהמודל."

    conn_err_msg = (
        "שגיאת חיבור ל-Anthropic. בדוק: 1) אינטרנט פעיל 2) חומת אש/פרוקסי "
        "3) Anthropic זמין באזור שלך. נסה שוב מאוחר יותר."
    )

    for attempt in range(3):  # 1 initial + 2 retries
        try:
            return _call()
        except anthropic.APITimeoutError as e:
            print("[APITimeoutError]", type(e).__name__, str(e))
            return "שגיאת זמן תגובה. החיבור איטי מדי. נסה שוב מאוחר יותר."
        except (anthropic.APIConnectionError, OSError, ConnectionError) as e:
            print(f"[ConnectionError attempt {attempt + 1}/3]", type(e).__name__, str(e))
            if attempt < 2:
                time.sleep(5)
                continue
            return conn_err_msg
        except anthropic.APIError as e:
            err_str = str(e).lower()
            if "429" in err_str or "rate" in err_str or "overloaded" in err_str:
                return "שגיאה: מכסה/עומס API. נסה שוב בעוד דקה."
            return f"שגיאת API: {e}"
        except Exception as e:
            err_str = str(e).lower()
            if "connection" in err_str or "connect" in err_str or "timeout" in err_str:
                if attempt < 2:
                    time.sleep(5)
                    continue
                return conn_err_msg
            return f"שגיאה בניתוח: {e}"

    return conn_err_msg
