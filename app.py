"""
Senior Product Manager Agent - Streamlit UI.

Entry point for the PM analysis tool.
Run: streamlit run app.py

Uses Anthropic (via analyzer) and Firecrawl (via scraper), both with API keys from .env.
"""

from pathlib import Path

from dotenv import load_dotenv

# Load .env first so analyzer and scraper get keys from env
load_dotenv(Path(__file__).resolve().parent / ".env")

import os
import time
import streamlit as st

from google_exporter import export_to_google_docs, check_credentials_status

# Debug: verify API keys loaded (prints to terminal, not UI)
print(f"Firecrawl Key Loaded: {bool(os.getenv('FIRECRAWL_API_KEY'))}")
print(f"Anthropic Key Loaded: {bool(os.getenv('ANTHROPIC_API_KEY'))}")

from analyzer import run_analysis
from schema import StrategicProductReport
from scraper import scrape_urls

# Page config - set before any other st calls
st.set_page_config(
    page_title="מנתח מוצרים אסטרטגי | Strategic Product Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Login password (override with APP_PASSWORD in .env for production)
LOGIN_PASSWORD = os.getenv("APP_PASSWORD", "Snati#3155")


def login_page() -> bool:
    """Show password login - dark theme to match site."""
    st.markdown(
        """
        <style>
        /* Dark background - match site */
        [data-testid="stAppViewContainer"] { background: #0e1117 !important; }
        /* Dark card - slightly lighter gray */
        .login-card-wrap {
            max-width: 400px;
            margin: 3rem auto 2rem;
            background: #262730 !important;
            padding: 2.5rem 2.5rem 2rem !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important;
            border: 1px solid #31333f !important;
        }
        .login-tag {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            direction: rtl;
        }
        .login-title { font-size: 1.6rem; font-weight: 700; color: #ffffff !important; margin: 0 0 0.5rem 0; text-align: center; direction: rtl; }
        .login-sub { font-size: 0.9rem; color: #9ca3af !important; margin: 0 0 1.5rem 0; text-align: center; direction: rtl; }
        /* Form block - dark gray */
        .login-card-wrap { padding-bottom: 2rem !important; }
        .block-container > div > div:nth-child(2) {
            margin-top: -2.5rem;
            max-width: 400px;
            margin-left: auto !important;
            margin-right: auto !important;
            padding: 0 2.5rem 1.5rem !important;
            background: #262730 !important;
            border-radius: 0 0 16px 16px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4);
            border: 1px solid #31333f;
            border-top: none !important;
        }
        .block-container > div > div:first-child .login-card-wrap { border-radius: 16px 16px 0 0 !important; margin-bottom: 0 !important; }
        /* Input dark theme on login page */
        .block-container > div > div:nth-child(2) [data-testid="stTextInput"] input { background: #1e1e1e !important; color: #fff !important; border-color: #31333f !important; }
        .block-container > div > div:nth-child(2) [data-testid="stTextInput"] input::placeholder { color: #9ca3af !important; }
        </style>
        <div class="login-card-wrap">
            <span class="login-tag">מנתח מוצרים אסטרטגי</span>
            <h1 class="login-title">כניסה | Sign In</h1>
            <p class="login-sub">הזן סיסמה לגישה | Enter your password to access</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Form in center column - will appear below card, same width
    _, col_form, _ = st.columns([1, 1, 1])
    with col_form:
        pwd = st.text_input("סיסמה", type="password", key="login_pwd", placeholder="הזן סיסמה | Enter password", label_visibility="collapsed")
        if st.button("התחבר | Sign In", type="primary", use_container_width=True, key="login_btn"):
            if pwd == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("סיסמה שגויה | Wrong password")
    return False


# Custom CSS - RTL Hebrew layout
st.markdown(
    """
    <style>
    /* Hide sidebar completely */
    [data-testid="stSidebar"] { display: none; }
    /* Root RTL - Hebrew format */
    html, body { direction: rtl !important; }
    /* Global RTL - all content right-to-left */
    [data-testid="stAppViewContainer"], .main, .main .block-container,
    div[data-testid="stVerticalBlock"] { direction: rtl !important; text-align: right !important; }
    /* Main title - push to right with flex */
    div[data-testid="stVerticalBlock"] > div:first-child,
    .block-container > div { direction: rtl !important; }
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    /* Markdown content - report & all text RTL */
    [data-testid="stMarkdown"], [data-testid="stMarkdown"] * { text-align: right !important; direction: rtl !important; }
    [data-testid="stMarkdown"] h1, [data-testid="stMarkdown"] h2, [data-testid="stMarkdown"] h3,
    [data-testid="stMarkdown"] h4, [data-testid="stMarkdown"] p, [data-testid="stMarkdown"] li,
    [data-testid="stMarkdown"] ul, [data-testid="stMarkdown"] ol { text-align: right !important; direction: rtl !important; }
    [data-testid="stMarkdown"] ul { padding-right: 1.5em; padding-left: 0; list-style-position: outside; }
    [data-testid="stMarkdown"] ol { padding-right: 1.5em; padding-left: 0; }
    /* Tables RTL */
    [data-testid="stMarkdown"] table { direction: rtl; text-align: right; }
    [data-testid="stMarkdown"] th, [data-testid="stMarkdown"] td { text-align: right !important; }
    /* Expanders - subtitles like קהל יעד, מודל עסקי */
    [data-testid="stExpander"] summary, [data-testid="stExpander"] label { direction: rtl !important; text-align: right !important; }
    [data-testid="stExpander"] > details { direction: rtl; }
    [data-testid="stExpander"] .streamlit-expanderContent { direction: rtl; text-align: right; }
    /* Input labels RTL */
    [data-testid="stTextInput"] label { direction: rtl; text-align: right; }
    /* Hide "Press Enter to apply" hint inside inputs */
    [data-testid="stTextInput"] [data-testid="InputInstructions"] { display: none !important; }
    [data-testid="stTextInput"] .st-emotion-cache-1gulkj5 { display: none !important; }
    /* Make input fields full width */
    [data-testid="stTextInput"] input { width: 100% !important; }
    .report-container { direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, sans-serif; }
    .report-section { margin: 1.5em 0; padding: 1em; border-radius: 8px; background: #f8f9fa; }
    .report-section h3 { color: #1e3a5f; border-bottom: 2px solid #1e3a5f; padding-bottom: 0.3em; }
    .report-section ul { padding-right: 1.5em; }
    .executive-summary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5em; border-radius: 10px; margin-bottom: 2em; }
    .comparison-table { width: 100%; border-collapse: collapse; margin: 1em 0; direction: rtl; }
    .comparison-table th, .comparison-table td { border: 1px solid #ddd; padding: 0.75em; text-align: right; }
    .comparison-table th { background: #1e3a5f; color: white; }
    .product-header { color: #764ba2; font-size: 1.2em; font-weight: bold; margin-top: 1.5em; }
    </style>
    """,
    unsafe_allow_html=True,
)


def main() -> None:
    # Login gate
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        login_page()
        return

    # Logout button - top left (second column = left in RTL)
    _, logout_col = st.columns([5, 1])
    with logout_col:
        if st.button("🚪 התנתק | Sign out", key="logout"):
            st.session_state.authenticated = False
            st.rerun()

    # Title - on right (in RTL, first column = right)
    title_col, _ = st.columns([4, 1])
    with title_col:
        st.markdown(
            '<h1 style="margin:0; text-align:right; direction:rtl;">📊 מנתח מוצרים אסטרטגי</h1>',
            unsafe_allow_html=True,
        )
    st.caption("Senior PM Agent (Claude) • Product Strategy • UX Friction • Business Models")

    # Initialize session state for competitor URLs
    if "competitor_urls" not in st.session_state:
        st.session_state.competitor_urls = []

    # Add Competitor button - at top, before URL inputs
    if st.button("➕ הוסף מתחרה", key="add_competitor"):
        st.session_state.competitor_urls.append("")
        st.rerun()

    # Product URL input
    main_url = st.text_input(
        "🔗 כתובת מוצר",
        placeholder="https://example-product.com",
        help="הכנס את כתובת האתר של המוצר לניתוח.",
    )

    # Dynamic competitor URL fields with delete button
    competitor_inputs = []
    for i in range(len(st.session_state.competitor_urls)):
        row_col1, row_col2 = st.columns([6, 1])
        with row_col1:
            val = st.text_input(
                f"מתחרה {i + 1}",
                value=st.session_state.competitor_urls[i],
                key=f"competitor_{i}",
                placeholder="https://competitor.com",
            )
        with row_col2:
            if st.button("✕", key=f"del_competitor_{i}", help="מחק שורה"):
                st.session_state.competitor_urls.pop(i)
                st.rerun()
        competitor_inputs.append(val)

    # Update session state with current values
    st.session_state.competitor_urls = competitor_inputs

    # Collect all URLs (main + competitors)
    all_urls = [u for u in [main_url] + competitor_inputs if u and u.strip()]

    st.divider()

    # Run Analysis - small button
    btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 2])
    with btn_col2:
        run_clicked = st.button("▶️ הרץ ניתוח", type="primary", use_container_width=True)
    if run_clicked:
        if not all_urls:
            st.warning("נא להזין לפחות כתובת מוצר אחת.")
            return

        with st.spinner("Scraping URLs..."):
            try:
                results = scrape_urls(all_urls)
            except ValueError as e:
                st.error(str(e))
                return

        # Check for scrape failures - show graceful Hebrew warning when site blocks
        failed = [r for r in results if not r.success]
        if failed:
            st.warning("נראה שהאתר חוסם סריקה אוטומטית, מנסה שיטת סריקה עוקפת...")
            for r in failed:
                st.error(f"Failed to scrape {r.url}: {r.error}")
        successful = [r for r in results if r.success]
        if not successful:
            st.error("No URLs could be scraped. Check your FIRECRAWL_API_KEY and URLs.")
            return

        # Paid API: combine all URLs, 15k chars total; short pause
        with st.spinner("Preparing analysis..."):
            time.sleep(2)

        # Prepare data for analysis
        limit_total = 15_000
        parts = []
        remaining = limit_total
        for r in successful:
            md = (r.markdown or "")[:remaining]
            parts.append(f"--- {r.url} ---\n{md}")
            remaining -= len(md)
            if remaining <= 0:
                break
        scraped_data = "\n\n".join(parts)
        
        # Debug: Show what we're sending
        debug_expander = st.expander("🔧 Debug Info", expanded=True)
        with debug_expander:
            # Check API key
            api_key_env = os.getenv("ANTHROPIC_API_KEY", "")
            api_key_secret = ""
            try:
                if hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
                    api_key_secret = st.secrets['ANTHROPIC_API_KEY']
            except:
                pass
            
            st.write(f"**API Key from .env:** {'✅ Found' if api_key_env else '❌ Not found'} ({len(api_key_env)} chars)")
            st.write(f"**API Key from secrets:** {'✅ Found' if api_key_secret else '❌ Not found'} ({len(api_key_secret)} chars)")
            st.write(f"**Scraped data length:** {len(scraped_data)} chars")
            st.write(f"**Cloud mode:** {os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false')}")
            
            # Show first 500 chars of scraped data
            st.write("**Scraped preview:**")
            st.code(scraped_data[:500] + "..." if len(scraped_data) > 500 else scraped_data)
        
        with st.spinner("Running PM Agent (Claude)... זה יכול לקחת עד 2 דקות"):
            try:
                start_time = time.time()
                report = run_analysis(scraped_data)
                elapsed = time.time() - start_time
                
                with debug_expander:
                    st.write(f"**Analysis time:** {elapsed:.1f} seconds")
                    st.write(f"**Report length:** {len(report) if report else 0} chars")
                
                if not report or not report.strip():
                    st.error("לא התקבלה תשובה מהמודל.")
                    return
                if report.strip().startswith("שגיאה") or report.strip().startswith("שגיאת"):
                    st.error(report)
                    with debug_expander:
                        st.write(f"**Error response:** {report}")
                    return
            except ValueError as e:
                st.error(str(e))
                return
            except Exception as e:
                err_str = str(e).lower()
                with debug_expander:
                    st.write(f"**Exception:** {type(e).__name__}: {e}")
                if "429" in err_str or "rate" in err_str or "overloaded" in err_str:
                    st.error("שגיאה: עומס API. נסה שוב בעוד דקה.")
                    return
                if "api_key" in err_str or "unauthorized" in err_str:
                    st.error("שגיאה: ANTHROPIC_API_KEY לא תקין או חסר.")
                    return
                st.error(f"שגיאה: {e}")
                return

        st.session_state.report = report
        st.rerun()

    # Display report if available
    if "report" in st.session_state:
        display_report(st.session_state.report)


def display_report(report) -> None:
    """Render the analysis result. Handles both plain string and StrategicProductReport."""
    st.divider()
    st.markdown(
        '<h2 style="text-align:right; direction:rtl;">📋 דוח מוצר אסטרטגי | Strategic Product Report</h2>',
        unsafe_allow_html=True,
    )
    # Handle plain string from run_analysis (RTL via global CSS)
    if isinstance(report, str):
        st.markdown(report)
        
        # Google Docs export button
        st.markdown("")  # Spacer
        if st.button("📄 הפץ ל-Docs", key="export_docs_str", use_container_width=False):
            with st.spinner("מייצא לגוגל דוקס..."):
                doc_url, error = export_to_google_docs(report)
                if doc_url:
                    st.success(f"הדוח נוצר בהצלחה! [פתח את המסמך]({doc_url})")
                    st.session_state.last_doc_url = doc_url
                else:
                    st.error(error or "לא ניתן לייצא. בדוק את ה-credentials.")
        
        # Show last created doc link if exists
        if "last_doc_url" in st.session_state:
            st.markdown(f"[🔗 קישור לדוח האחרון]({st.session_state.last_doc_url})")
        
        # Clear report button
        if st.button("🗑️ נקה דוח", key="clear_str"):
            if "report" in st.session_state:
                del st.session_state.report
            if "last_doc_url" in st.session_state:
                del st.session_state.last_doc_url
            st.rerun()
        return

    # Structured report (StrategicProductReport)
    st.markdown('<div class="report-container" dir="rtl">', unsafe_allow_html=True)
    if report.executive_summary:
        st.markdown(
            f'<div class="executive-summary"><strong>סיכום מנהלים</strong><br>{report.executive_summary}</div>',
            unsafe_allow_html=True,
        )

    for pa in report.product_analyses:
        st.markdown(
            f'<div class="product-header">{pa.product_name} ({pa.product_url})</div>',
            unsafe_allow_html=True,
        )

        with st.expander(f"מהות המוצר | {pa.product_name}", expanded=True):
            st.markdown(f"**תיאור:** {pa.essence.description}")
            st.markdown(f"**בעיה שנפתרת:** {pa.essence.problem_solved}")

        with st.expander("אסטרטגיה", expanded=True):
            st.markdown(f"**קהל יעד:** {pa.strategy.target_audience}")
            st.markdown(f"**מיצוב:** {pa.strategy.positioning}")
            st.markdown(f"**מודל עסקי:** {pa.strategy.business_model}")

        with st.expander("מפת יכולות"):
            if pa.feature_inventory:
                st.markdown("\n".join(f"- {f}" for f in pa.feature_inventory))
            else:
                st.info("לא זוהו יכולות.")

        with st.expander("נקודות חוזק וחולשה"):
            st.markdown("**חוזקות:**")
            if pa.strengths_weaknesses.strengths:
                st.markdown("\n".join(f"- {s}" for s in pa.strengths_weaknesses.strengths))
            else:
                st.markdown("- *לא זוהו*")
            st.markdown("**חולשות:**")
            if pa.strengths_weaknesses.weaknesses:
                st.markdown("\n".join(f"- {w}" for w in pa.strengths_weaknesses.weaknesses))
            else:
                st.markdown("- *לא זוהו*")

        with st.expander("QA ואופטימיזציה"):
            st.markdown("**נקודות חיכוך:**")
            if pa.qa_optimization.friction_points:
                st.markdown("\n".join(f"- {f}" for f in pa.qa_optimization.friction_points))
            else:
                st.markdown("- *לא זוהו*")
            st.markdown("**הצעות לשיפור:**")
            if pa.qa_optimization.suggestions:
                st.markdown("\n".join(f"- {s}" for s in pa.qa_optimization.suggestions))
            else:
                st.markdown("- *לא זוהו*")

    # Comparison table (when multiple products)
    if report.comparison_table:
        st.markdown("## 📊 טבלת השוואה")
        n_cols = max((len(r.values) for r in report.comparison_table), default=1)
        headers = ["מימד"] + [f"מוצר {i+1}" for i in range(n_cols)]
        rows = [[r.dimension] + (r.values + [""] * (n_cols - len(r.values)))[:n_cols] for r in report.comparison_table]
        table_md = "| " + " | ".join(headers) + " |\n"
        table_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for row in rows:
            table_md += "| " + " | ".join(str(c) for c in row) + " |\n"
        st.markdown(table_md)

    st.markdown("</div>", unsafe_allow_html=True)

    # Convert structured report to text for export
    def structured_to_text(rep) -> str:
        lines = []
        if rep.executive_summary:
            lines.append(f"סיכום מנהלים\n{rep.executive_summary}\n")
        for pa in rep.product_analyses:
            lines.append(f"\n{pa.product_name} ({pa.product_url})\n")
            lines.append(f"תיאור: {pa.essence.description}")
            lines.append(f"בעיה שנפתרת: {pa.essence.problem_solved}\n")
            lines.append(f"קהל יעד: {pa.strategy.target_audience}")
            lines.append(f"מיצוב: {pa.strategy.positioning}")
            lines.append(f"מודל עסקי: {pa.strategy.business_model}\n")
            if pa.feature_inventory:
                lines.append("יכולות:")
                lines.extend(f"  - {f}" for f in pa.feature_inventory)
            if pa.strengths_weaknesses.strengths:
                lines.append("\nחוזקות:")
                lines.extend(f"  - {s}" for s in pa.strengths_weaknesses.strengths)
            if pa.strengths_weaknesses.weaknesses:
                lines.append("\nחולשות:")
                lines.extend(f"  - {w}" for w in pa.strengths_weaknesses.weaknesses)
            if pa.qa_optimization.friction_points:
                lines.append("\nנקודות חיכוך:")
                lines.extend(f"  - {f}" for f in pa.qa_optimization.friction_points)
            if pa.qa_optimization.suggestions:
                lines.append("\nהצעות לשיפור:")
                lines.extend(f"  - {s}" for s in pa.qa_optimization.suggestions)
        return "\n".join(lines)

    # Google Docs export button
    st.markdown("")  # Spacer
    if st.button("📄 הפץ ל-Docs", key="export_docs_struct", use_container_width=False):
        with st.spinner("מייצא לגוגל דוקס..."):
            report_text = structured_to_text(report)
            doc_url, error = export_to_google_docs(report_text)
            if doc_url:
                st.success(f"הדוח נוצר בהצלחה! [פתח את המסמך]({doc_url})")
                st.session_state.last_doc_url = doc_url
            else:
                st.error(error or "לא ניתן לייצא. בדוק את ה-credentials.")
    
    # Show last created doc link if exists
    if "last_doc_url" in st.session_state:
        st.markdown(f"[🔗 קישור לדוח האחרון]({st.session_state.last_doc_url})")

    # Clear report button
    if st.button("🗑️ נקה דוח", key="clear_struct"):
        if "report" in st.session_state:
            del st.session_state.report
        if "last_doc_url" in st.session_state:
            del st.session_state.last_doc_url
        st.rerun()


if __name__ == "__main__":
    main()
