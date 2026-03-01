"""
Senior Product Manager Agent - LLM analysis via Anthropic Claude.

Persona: Senior PM (10 years experience). Focus: Product Strategy, Value Proposition, QA friction points.
Output: Detailed structured Markdown in HEBREW.
Requires ANTHROPIC_API_KEY in .env or Streamlit secrets.
"""

from dotenv import load_dotenv
from pathlib import Path

# Load .env BEFORE any environment variables are accessed
load_dotenv(Path(__file__).resolve().parent / ".env")

import os
import re
import time
import socket

# Detect if running in cloud environment
def _is_cloud_environment():
    """Check if we're running in Streamlit Cloud or similar."""
    # Streamlit Cloud sets these
    if os.environ.get('STREAMLIT_SERVER_HEADLESS') == 'true':
        return True
    # Check for common cloud indicators
    if os.environ.get('STREAMLIT_SHARING_MODE'):
        return True
    if os.environ.get('IS_CLOUD'):
        return True
    return False

IS_CLOUD = _is_cloud_environment()

# DNS workaround: Only for LOCAL environments with network restrictions
# In cloud, use normal DNS resolution
if not IS_CLOUD:
    _ANTHROPIC_IP_CACHE = None
    _original_getaddrinfo = socket.getaddrinfo

    def _patched_getaddrinfo(host, port, *args, **kwargs):
        global _ANTHROPIC_IP_CACHE
        if host == 'api.anthropic.com':
            if _ANTHROPIC_IP_CACHE is None:
                try:
                    results = _original_getaddrinfo(host, port, socket.AF_INET, *args[1:] if len(args) > 1 else (), **kwargs)
                    if results:
                        _ANTHROPIC_IP_CACHE = results[0][4][0]
                except:
                    pass
            if _ANTHROPIC_IP_CACHE:
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (_ANTHROPIC_IP_CACHE, port))]
        return _original_getaddrinfo(host, port, *args, **kwargs)

    socket.getaddrinfo = _patched_getaddrinfo
    print("[Analyzer] Local mode: DNS workaround enabled")
else:
    print("[Analyzer] Cloud mode: Using standard networking")

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


def _get_api_key() -> str:
    """Get Anthropic API key from env or Streamlit secrets."""
    # Try environment variable first
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    
    # Try Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
            return st.secrets['ANTHROPIC_API_KEY'].strip()
    except:
        pass
    
    return ""


def run_analysis(scraped_data: str) -> str:
    """
    Run PM analysis via Anthropic Claude.
    Uses ANTHROPIC_API_KEY from .env or Streamlit secrets.
    Returns Markdown report in Hebrew, or error message string.
    """
    import sys
    
    def _debug(msg):
        """Print debug message to console and return for potential UI display."""
        print(f"[Analyzer] {msg}")
        sys.stdout.flush()
        return msg
    
    _debug("Starting analysis...")
    
    try:
        import anthropic
        _debug(f"Anthropic SDK version: {anthropic.__version__}")
    except ImportError:
        return "שגיאה: anthropic לא מותקן. הרץ: pip install anthropic"

    key = _get_api_key()
    if not key:
        return "שגיאה: ANTHROPIC_API_KEY לא נמצא. הוסף אותו ל-.env או ל-Streamlit Secrets."
    
    _debug(f"API key found: {key[:15]}...{key[-4:]} (length: {len(key)})")

    clean_text = _clean_scraped_markdown(str(scraped_data or ""))
    if not clean_text.strip():
        return "שגיאה: לא נמצא תוכן לניתוח לאחר הניקוי."
    
    _debug(f"Clean text length: {len(clean_text)} chars")

    user_content = f"Product website data to analyze:\n\n---\n\n{clean_text}"

    # Configure client based on environment
    timeout_seconds = 240  # 4 minutes for both local and cloud
    
    _debug(f"IS_CLOUD: {IS_CLOUD}, timeout: {timeout_seconds}s")
    
    try:
        import httpx
        _debug(f"httpx version: {httpx.__version__}")
        # In cloud: use default settings
        # Locally: force HTTP/1.1 to avoid network issues
        if IS_CLOUD:
            http_client = httpx.Client(timeout=timeout_seconds)
            _debug("Using default httpx client for cloud")
        else:
            http_client = httpx.Client(
                timeout=timeout_seconds,
                http1=True,
                http2=False,
                trust_env=False
            )
            _debug("Using HTTP/1.1 httpx client for local")
        client = anthropic.Anthropic(
            api_key=key,
            http_client=http_client,
        )
    except ImportError:
        _debug("httpx not available, using default client")
        client = anthropic.Anthropic(
            api_key=key,
            timeout=timeout_seconds,
        )

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6").strip()
    if not model:
        model = "claude-sonnet-4-6"

    _debug(f"Using model: {model}")

    def _call():
        response = client.messages.create(
            model=model,
            max_tokens=8192,
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
        "שגיאת חיבור ל-Anthropic. בדוק: 1) מפתח API תקין 2) חיבור אינטרנט "
        "3) נסה שוב בעוד דקה."
    )

    for attempt in range(3):  # 1 initial + 2 retries
        try:
            _debug(f"Attempt {attempt + 1}/3 - calling Anthropic API...")
            import time as time_module
            call_start = time_module.time()
            result = _call()
            call_duration = time_module.time() - call_start
            _debug(f"Success! Duration: {call_duration:.1f}s, Response length: {len(result)}")
            return result
        except anthropic.APITimeoutError as e:
            _debug(f"APITimeoutError: {e}")
            if attempt < 2:
                _debug("Retrying after timeout...")
                time.sleep(3)
                continue
            return f"שגיאת זמן תגובה ({timeout_seconds}s). הניתוח לוקח יותר מדי זמן. נסה עם URL קצר יותר."
        except anthropic.APIConnectionError as e:
            _debug(f"APIConnectionError attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(5)
                continue
            return f"שגיאת חיבור: {str(e)[:200]}"
        except anthropic.AuthenticationError as e:
            _debug(f"AuthenticationError: {e}")
            return f"שגיאת אימות: מפתח ה-API לא תקין. בדוק את ANTHROPIC_API_KEY. ({str(e)[:100]})"
        except anthropic.RateLimitError as e:
            _debug(f"RateLimitError: {e}")
            if attempt < 2:
                _debug("Rate limited, waiting 10s...")
                time.sleep(10)
                continue
            return "שגיאה: חריגה ממגבלת הבקשות. נסה שוב בעוד דקה."
        except anthropic.APIError as e:
            err_str = str(e).lower()
            _debug(f"APIError: {e}")
            if "429" in err_str or "rate" in err_str or "overloaded" in err_str:
                if attempt < 2:
                    time.sleep(10)
                    continue
                return "שגיאה: עומס על ה-API. נסה שוב בעוד דקה."
            return f"שגיאת API: {str(e)[:300]}"
        except Exception as e:
            _debug(f"Unexpected error: {type(e).__name__}: {e}")
            err_str = str(e).lower()
            if "connection" in err_str or "connect" in err_str or "timeout" in err_str:
                if attempt < 2:
                    time.sleep(5)
                    continue
                return f"שגיאת חיבור: {str(e)[:200]}"
            return f"שגיאה בניתוח: {type(e).__name__}: {str(e)[:200]}"

    return conn_err_msg
