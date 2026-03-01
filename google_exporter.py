"""
Google Docs Export Module with OAuth2.

Creates Google Docs from report content using user's Google account.
Requires OAuth2 credentials JSON file.
"""

import os
import time
from pathlib import Path
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# OAuth2 credential files
OAUTH_CREDENTIALS_FILE = "oauth_credentials.json"
TOKEN_FILE = "token.json"

# Required Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]


def _get_credentials():
    """
    Load or create OAuth2 credentials.
    
    On first run, opens browser for Google login.
    Subsequent runs use saved token.
    
    Returns:
        Credentials or None if not available
    """
    project_root = Path(__file__).resolve().parent
    token_path = project_root / TOKEN_FILE
    oauth_path = project_root / OAUTH_CREDENTIALS_FILE
    
    creds = None
    
    # Load existing token if available
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            print(f"[Google Exporter] Failed to load token: {e}")
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[Google Exporter] Token refresh failed: {e}")
                creds = None
        
        if not creds:
            if not oauth_path.exists():
                print(f"[Google Exporter] OAuth credentials file not found: {oauth_path}")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(oauth_path), SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"[Google Exporter] OAuth flow failed: {e}")
                return None
        
        # Save token for future use
        if creds:
            try:
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
            except Exception as e:
                print(f"[Google Exporter] Failed to save token: {e}")
    
    return creds


def export_to_google_docs(
    report_content: str,
    title: Optional[str] = None,
    share_email: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """
    Export report content to a new Google Doc.
    
    Args:
        report_content: The text content to insert into the document
        title: Optional document title (default: "דוח ניתוח מוצר - {timestamp}")
        share_email: Unused (kept for API compatibility)
    
    Returns:
        Tuple of (document_url, error_message)
        - On success: (url, None)
        - On failure: (None, error_message)
    """
    # Get credentials
    credentials = _get_credentials()
    if not credentials:
        return None, "לא נמצאו credentials. וודא שקובץ oauth_credentials.json קיים ואושר."
    
    try:
        # Build services
        docs_service = build("docs", "v1", credentials=credentials)
        drive_service = build("drive", "v3", credentials=credentials)
        
        # Create document title
        if not title:
            title = f"דוח ניתוח מוצר - {time.strftime('%Y-%m-%d %H:%M')}"
        
        # Get folder ID from environment (optional)
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        
        # Create the document via Drive API
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
        }
        if folder_id:
            file_metadata["parents"] = [folder_id]
        
        file = drive_service.files().create(
            body=file_metadata,
            fields="id"
        ).execute()
        doc_id = file.get("id")
        
        if not doc_id:
            return None, "נכשל ביצירת המסמך - לא התקבל מזהה מסמך."
        
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
        docs_service.documents().batchUpdate(
            documentId=doc_id, 
            body={"requests": requests}
        ).execute()
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return doc_url, None
        
    except HttpError as e:
        error_msg = str(e)
        if "403" in error_msg:
            return None, "שגיאת הרשאות (403). נסה להתחבר מחדש."
        if "401" in error_msg:
            return None, "שגיאת אימות (401). נסה להתחבר מחדש."
        return None, f"שגיאת Google API: {error_msg}"
    except Exception as e:
        return None, f"שגיאה בייצוא: {str(e)}"


def check_credentials_status() -> tuple[bool, str]:
    """
    Check if Google credentials are properly configured.
    
    Returns:
        Tuple of (is_configured, status_message)
    """
    project_root = Path(__file__).resolve().parent
    oauth_path = project_root / OAUTH_CREDENTIALS_FILE
    token_path = project_root / TOKEN_FILE
    
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds and creds.valid:
                return True, "מחובר ל-Google ומוכן לייצוא."
            elif creds and creds.expired and creds.refresh_token:
                return True, "Token פג תוקף אך ניתן לרענן."
        except Exception:
            pass
    
    if oauth_path.exists():
        return False, "נדרשת התחברות ל-Google. לחץ על 'הפץ ל-Docs' להתחברות."
    
    return False, "לא נמצא קובץ oauth_credentials.json"
