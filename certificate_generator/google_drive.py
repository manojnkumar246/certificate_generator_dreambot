"""Google Drive integration for automatic certificate uploads and public link generation."""

from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/drive"]
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.pickle"


def get_drive_service():
    """Authenticate and return Google Drive service."""
    creds = None

    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json not found. Set up OAuth2 credentials at "
                    "https://console.cloud.google.com/apis/credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def create_or_get_certificates_folder(service) -> str:
    """Find or create 'DreambotCertificates' folder and return its ID."""
    try:
        query = "name='DreambotCertificates' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=1,
        ).execute()

        files = results.get("files", [])
        if files:
            return files[0]["id"]

        # Create folder if it doesn't exist
        file_metadata = {
            "name": "DreambotCertificates",
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=file_metadata, fields="id").execute()
        folder_id = folder.get("id")

        # Share the folder publicly
        share_permission = {
            "type": "anyone",
            "role": "reader",
        }
        service.permissions().create(
            fileId=folder_id,
            body=share_permission,
            fields="id",
        ).execute()

        return folder_id
    except HttpError as error:
        raise RuntimeError(f"Google Drive API error: {error}")


def upload_certificate_to_drive(
    service,
    folder_id: str,
    file_path: Path,
    certificate_uid: str,
) -> str:
    """Upload certificate to Google Drive and return public shareable link."""
    try:
        file_metadata = {
            "name": f"{certificate_uid}.jpg",
            "parents": [folder_id],
        }
        media = MediaFileUpload(file_path, mimetype="image/jpeg", resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()

        file_id = file.get("id")

        # Make file publicly readable
        share_permission = {
            "type": "anyone",
            "role": "reader",
        }
        service.permissions().create(
            fileId=file_id,
            body=share_permission,
            fields="id",
        ).execute()

        # Generate public shareable link
        public_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        return public_url

    except HttpError as error:
        raise RuntimeError(f"Failed to upload certificate to Google Drive: {error}")


def get_public_drive_url(service) -> str:
    """Get the public URL of the DreambotCertificates folder."""
    folder_id = create_or_get_certificates_folder(service)
    return f"https://drive.google.com/drive/folders/{folder_id}?usp=sharing"
