from __future__ import annotations

import ipaddress
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
SENDER_EMAIL = "dreambotcertificates6@gmail.com"
def get_smtp_app_password() -> str:
    """Load the SMTP app password from the project .env or environment."""
    load_dotenv(dotenv_path=ENV_FILE, override=False)
    return os.getenv("APP_PASSWORD", "").strip()


def get_public_app_url() -> str | None:
    """Return the hosted app URL used to make recipient certificate links."""
    load_dotenv(dotenv_path=ENV_FILE, override=False)
    base_url = (
        os.getenv("APP_PUBLIC_URL", "").strip()
        or os.getenv("RENDER_EXTERNAL_URL", "").strip()
    ).rstrip("/")
    if not base_url:
        return None

    parsed = urlsplit(base_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "APP_PUBLIC_URL must be a public HTTPS app URL without credentials, "
            "query, or fragment."
        )
    hostname = parsed.hostname
    if hostname is None or hostname.lower() == "localhost" or hostname.endswith(
        (".localhost", ".local")
    ):
        raise ValueError("APP_PUBLIC_URL must not point to a local host.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise ValueError("APP_PUBLIC_URL must use a public IP address.")
    return base_url


def get_app_admin_password() -> str:
    """Load the admin password used to protect the hosted management UI."""
    load_dotenv(dotenv_path=ENV_FILE, override=False)
    return os.getenv("APP_ADMIN_PASSWORD", "").strip()
