"""
Google Docs Export Module - Cloud-Native OAuth2.

Supports both Streamlit Cloud (via secrets) and local development (via files).
Priority: Streamlit Secrets > Local token.json > OAuth flow (local only)
"""

import os
import json
import time
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# File paths for local development only
OAUTH_CREDENTIALS_FILE = "oauth_credentials.json"
TOKEN_FILE = "token.json"

# Required Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

# Debug flag - set to True to see debug messages in Streamlit
DEBUG_MODE = True


def _log(message: str):
    """Log message to console and optionally to Streamlit."""
    print(f"[Google Exporter] {message}")
    if DEBUG_MODE:
        try:
            import streamlit as st
            st.info(f"🔧 Debug: {message}")
        except:
            pass


def _get_credentials():
    """
    Get OAuth2 credentials - Cloud-Native approach.
    
    Priority:
    1. Streamlit Secrets (GOOGLE_TOKEN_JSON) - for cloud deployment
    2. Local token.json file - for local development  
    3. OAuth browser flow - for initial local setup only
    
    Returns:
        Credentials object or None
    """
    creds = None
    source = None
    
    # ============================================
    # PRIORITY 1: Streamlit Secrets (Cloud-Native)
    # ============================================
    try:
        import streamlit as st
        
        # Check for GOOGLE_TOKEN_JSON (single JSON string - recommended)
        if hasattr(st, 'secrets') and 'GOOGLE_TOKEN_JSON' in st.secrets:
            _log("Found GOOGLE_TOKEN_JSON in Streamlit secrets")
            token_json_str = st.secrets['GOOGLE_TOKEN_JSON']
            token_dict = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
            source = "Streamlit Secrets (GOOGLE_TOKEN_JSON)"
            _log(f"Successfully loaded credentials from {source}")
        
        # Alternative: Check for GOOGLE_TOKEN table (TOML format)
        elif hasattr(st, 'secrets') and 'GOOGLE_TOKEN' in st.secrets:
            _log("Found GOOGLE_TOKEN table in Streamlit secrets")
            token_data = st.secrets['GOOGLE_TOKEN']
            
            # Convert AttrDict to regular dict
            if hasattr(token_data, 'to_dict'):
                token_dict = token_data.to_dict()
            else:
                token_dict = dict(token_data)
            
            # Handle scopes if it's a string
            if 'scopes' in token_dict and isinstance(token_dict['scopes'], str):
                token_dict['scopes'] = json.loads(token_dict['scopes'])
            
            creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
            source = "Streamlit Secrets (GOOGLE_TOKEN)"
            _log(f"Successfully loaded credentials from {source}")
            
    except ImportError:
        _log("Streamlit not available - running outside Streamlit context")
    except Exception as e:
        _log(f"Failed to load from Streamlit secrets: {type(e).__name__}: {e}")
    
    # If we got credentials from secrets, handle refresh and return
    if creds:
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    _log("Token expired, refreshing...")
                    creds.refresh(Request())
                    _log("Token refreshed successfully")
                except Exception as e:
                    _log(f"Token refresh failed: {e}")
                    return None
            else:
                _log("Token invalid and cannot be refreshed")
                return None
        return creds
    
    # ============================================
    # PRIORITY 2: Local token.json file
    # ============================================
    project_root = Path(__file__).resolve().parent
    token_path = project_root / TOKEN_FILE
    
    if token_path.exists():
        try:
            _log(f"Loading from local {TOKEN_FILE}")
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            source = f"Local {TOKEN_FILE}"
            
            # Refresh if needed
            if creds and not creds.valid:
                if creds.expired and creds.refresh_token:
                    _log("Token expired, refreshing...")
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(token_path, "w") as f:
                        f.write(creds.to_json())
                    _log("Token refreshed and saved")
            
            if creds and creds.valid:
                _log(f"Successfully loaded credentials from {source}")
                return creds
        except Exception as e:
            _log(f"Failed to load from {TOKEN_FILE}: {e}")
    
    # ============================================
    # PRIORITY 3: OAuth flow (LOCAL ONLY)
    # ============================================
    oauth_path = project_root / OAUTH_CREDENTIALS_FILE
    
    # IMPORTANT: Only attempt OAuth flow if:
    # 1. oauth_credentials.json exists (meaning we're in local dev)
    # 2. We're NOT in a cloud environment
    if not oauth_path.exists():
        _log("No oauth_credentials.json found - cannot do OAuth flow")
        _log("For cloud deployment: Add GOOGLE_TOKEN_JSON to Streamlit secrets")
        return None
    
    # Check if we might be in cloud (no display available)
    is_likely_cloud = os.environ.get('STREAMLIT_SERVER_HEADLESS') == 'true'
    if is_likely_cloud:
        _log("Headless environment detected - skipping OAuth browser flow")
        return None
    
    try:
        _log("Starting OAuth browser flow for initial setup...")
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(oauth_path), SCOPES)
        creds = flow.run_local_server(port=0, timeout_seconds=120)
        
        # Save token for future use
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        _log(f"New token saved to {TOKEN_FILE}")
        return creds
        
    except Exception as e:
        _log(f"OAuth flow failed: {e}")
        return None


def export_to_google_docs(
    report_content: str,
    title: Optional[str] = None,
    share_email: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """
    Export report content to a new Google Doc.
    
    Args:
        report_content: The text content to insert
        title: Optional document title
        share_email: Unused (kept for compatibility)
    
    Returns:
        Tuple of (document_url, error_message)
    """
    _log("Starting Google Docs export...")
    
    # Get credentials
    credentials = _get_credentials()
    
    if not credentials:
        error_msg = "לא נמצאו credentials לחיבור ל-Google."
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                if 'GOOGLE_TOKEN_JSON' not in st.secrets and 'GOOGLE_TOKEN' not in st.secrets:
                    error_msg = "הוסף GOOGLE_TOKEN_JSON ל-Streamlit Secrets כדי לאפשר ייצוא."
                else:
                    error_msg = "ה-Token ב-Secrets לא תקין או פג תוקף. צור token חדש מקומית והעתק אותו."
        except:
            pass
        return None, error_msg
    
    _log("Credentials obtained successfully, creating document...")
    
    try:
        # Build services
        docs_service = build("docs", "v1", credentials=credentials)
        drive_service = build("drive", "v3", credentials=credentials)
        
        # Create document title
        if not title:
            title = f"דוח ניתוח מוצר - {time.strftime('%Y-%m-%d %H:%M')}"
        
        # Get folder ID from environment/secrets (optional)
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'GOOGLE_DRIVE_FOLDER_ID' in st.secrets:
                folder_id = st.secrets['GOOGLE_DRIVE_FOLDER_ID']
        except:
            pass
        
        # Create the document via Drive API
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]
        
        _log("Creating Google Doc...")
        file = drive_service.files().create(
            body=file_metadata,
            fields="id"
        ).execute()
        doc_id = file.get("id")
        
        if not doc_id:
            return None, "נכשל ביצירת המסמך - לא התקבל מזהה."
        
        _log(f"Document created with ID: {doc_id}")
        
        # Insert content with RTL formatting for Hebrew
        content_length = len(report_content)
        requests = [
            {
                "insertText": {
                    "location": {"index": 1},
                    "text": report_content
                }
            },
            {
                "updateParagraphStyle": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": content_length + 1
                    },
                    "paragraphStyle": {
                        "direction": "RIGHT_TO_LEFT",
                        "alignment": "START"
                    },
                    "fields": "direction,alignment"
                }
            }
        ]
        
        _log("Inserting content...")
        docs_service.documents().batchUpdate(
            documentId=doc_id, 
            body={"requests": requests}
        ).execute()
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        _log(f"Export successful! URL: {doc_url}")
        return doc_url, None
        
    except HttpError as e:
        error_msg = str(e)
        _log(f"HTTP Error: {error_msg}")
        if "403" in error_msg:
            return None, "שגיאת הרשאות (403). ה-Token אינו מורשה לפעולה זו."
        if "401" in error_msg:
            return None, "שגיאת אימות (401). ה-Token פג תוקף או לא תקין."
        return None, f"שגיאת Google API: {error_msg[:200]}"
    except Exception as e:
        _log(f"Error: {type(e).__name__}: {e}")
        return None, f"שגיאה בייצוא: {str(e)}"


def check_credentials_status() -> tuple[bool, str]:
    """Check if Google credentials are configured."""
    
    # Check Streamlit secrets first
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            if 'GOOGLE_TOKEN_JSON' in st.secrets:
                return True, "✅ GOOGLE_TOKEN_JSON מוגדר ב-Secrets"
            if 'GOOGLE_TOKEN' in st.secrets:
                return True, "✅ GOOGLE_TOKEN מוגדר ב-Secrets"
    except:
        pass
    
    # Check local token file
    project_root = Path(__file__).resolve().parent
    token_path = project_root / TOKEN_FILE
    
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds and (creds.valid or creds.refresh_token):
                return True, f"✅ {TOKEN_FILE} קיים ותקין"
        except:
            pass
    
    # Check if OAuth setup is possible
    oauth_path = project_root / OAUTH_CREDENTIALS_FILE
    if oauth_path.exists():
        return False, f"⚠️ נדרשת התחברות ראשונית. לחץ על 'הפץ ל-Docs'."
    
    return False, "❌ לא מוגדר חיבור ל-Google. הוסף GOOGLE_TOKEN_JSON ל-Secrets."
