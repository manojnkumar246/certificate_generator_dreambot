from __future__ import annotations

import calendar
import json
import re
import smtplib
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

import pandas as pd

from certificate_generator.emailing import connect_smtp, send_email
from certificate_generator.personalize_template import personalize_certificate
from certificate_generator.settings import get_public_app_url


REQUIRED_COLUMNS = ("Name", "Email", "Send", "Duration")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
CERTIFICATE_UID_PATTERN = re.compile(r"DB-WS7-\d{4}-[A-F0-9]{32}")
REPORT_COLUMNS = (
    "certificate_uid",
    "name",
    "email",
    "duration",
    "verification_url",
    "expires_at",
    "send_requested",
    "certificate_status",
    "email_status",
    "error",
)


@dataclass
class PreviewBatch:
    output_dir: Path
    report_path: Path
    archive_path: Path
    output_root: Path
    records: list[dict[str, str]]
    certificate_paths: dict[str, Path]
    has_public_url: bool

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def generated_count(self) -> int:
        return sum(
            record["certificate_status"] == "generated"
            for record in self.records
        )

    @property
    def emailed_count(self) -> int:
        return sum(record["email_status"] == "sent" for record in self.records)

    @property
    def skipped_count(self) -> int:
        return sum(record["email_status"] == "skipped" for record in self.records)

    @property
    def error_count(self) -> int:
        return sum(
            record["certificate_status"] == "failed"
            or record["email_status"] == "failed"
            for record in self.records
        )


def normalize_student_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize workbook headers to Name, Email, Send, and Duration."""
    aliases = {
        "name": "Name",
        "student_name": "Name",
        "email": "Email",
        "mail": "Email",
        "student_email": "Email",
        "send": "Send",
        "send_email": "Send",
        "status": "Send",
        "duration": "Duration",
        "workshop_duration": "Duration",
        "workshop duration": "Duration",
    }
    normalized = data.copy()
    normalized.columns = [
        aliases.get(str(column).strip().lower(), str(column).strip())
        for column in normalized.columns
    ]
    duplicated = normalized.columns[normalized.columns.duplicated()].tolist()
    if duplicated:
        raise ValueError(
            "Worksheet contains duplicate columns after normalization: "
            + ", ".join(sorted(set(duplicated)))
        )
    missing = [column for column in REQUIRED_COLUMNS if column not in normalized]
    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}. "
            "Expected Name, Email, Send, and Duration."
        )
    return normalized


def generate_previews(
    students: pd.DataFrame,
    template_path: Path | str,
    output_root: Path | str,
) -> PreviewBatch:
    """Create unique certificates and reports without making SMTP connections."""
    normalized = normalize_student_columns(students).copy()
    for column in REQUIRED_COLUMNS:
        normalized[column] = normalized[column].fillna("").astype(str).str.strip()

    timestamp = datetime.now().astimezone()
    run_id = timestamp.strftime("%Y%m%d_%H%M%S_%f")
    output_root = Path(output_root).resolve()
    output_dir = output_root / run_id
    certificate_dir = output_dir / "certificates"
    certificate_dir.mkdir(parents=True, exist_ok=False)

    public_app_url = get_public_app_url()
    records: list[dict[str, str]] = []
    certificate_paths: dict[str, Path] = {}

    for _, row in normalized.iterrows():
        name = row["Name"]
        duration = row["Duration"]
        uid = f"DB-WS7-{timestamp.year}-{uuid.uuid4().hex.upper()}"
        expires_at = _add_months(timestamp, 6)
        requested = row["Send"].lower() == "yes"
        verification_url = build_verification_url(uid, public_app_url)
        record = {
            "certificate_uid": uid,
            "name": name,
            "email": row["Email"],
            "duration": duration,
            "verification_url": verification_url,
            "expires_at": expires_at.isoformat(timespec="seconds"),
            "send_requested": "yes" if requested else "no",
            "certificate_status": "failed",
            "email_status": "pending_approval" if requested else "skipped",
            "error": "",
        }

        try:
            if not name:
                raise ValueError("Student name is empty.")
            if not duration:
                raise ValueError("Workshop duration is empty.")

            certificate_path = certificate_dir / f"{uid}.jpg"
            personalize_certificate(
                template_path,
                certificate_path,
                certificate_number=uid,
                student_name=name,
                workshop_duration=duration,
                certificate_url=verification_url,
            )
            record["certificate_status"] = "generated"
            certificate_paths[uid] = certificate_path
            _save_certificate_record(
                output_root,
                uid,
                name,
                expires_at,
                certificate_path,
            )
        except (OSError, ValueError) as error:
            record["error"] = f"Certificate generation failed: {error}"
            if requested:
                record["email_status"] = "not_attempted"

        records.append(record)

    archive_path = output_dir / "certificates.zip"
    _write_archive(archive_path, certificate_paths.values())
    report_path = output_dir / "delivery_report.csv"
    batch = PreviewBatch(
        output_dir=output_dir,
        report_path=report_path,
        archive_path=archive_path,
        output_root=output_root,
        records=records,
        certificate_paths=certificate_paths,
        has_public_url=public_app_url is not None,
    )
    _write_report(batch)
    return batch


def send_approved_emails(
    batch: PreviewBatch,
    sender_email: str,
    email_password: str,
) -> PreviewBatch:
    """Send only certificates whose generated previews were explicitly approved."""
    if not batch.has_public_url:
        raise ValueError(
            "Sending is disabled until APP_PUBLIC_URL points to the deployed "
            "HTTPS application. Configure it and generate a new batch."
        )
    if not email_password:
        raise ValueError("APP_PASSWORD is not configured.")

    smtp_server: smtplib.SMTP | None = None
    for record in batch.records:
        if (
            record["send_requested"] != "yes"
            or record["certificate_status"] != "generated"
            or record["email_status"] != "pending_approval"
        ):
            continue
        if not EMAIL_PATTERN.fullmatch(record["email"]):
            record["email_status"] = "failed"
            record["error"] = _append_error(
                record["error"], f"Invalid email address: {record['email']}"
            )
            continue

        if smtp_server is None:
            try:
                smtp_server = connect_smtp(sender_email, email_password)
            except (OSError, smtplib.SMTPException) as error:
                record["email_status"] = "failed"
                record["error"] = _append_error(
                    record["error"], f"SMTP connection failed: {error}"
                )
                continue

        try:
            certificate_path = batch.certificate_paths[record["certificate_uid"]]
            send_email(
                sender_email,
                record["email"],
                record["name"],
                certificate_path.read_bytes(),
                smtp_server,
                verification_url=record["verification_url"],
            )
            record["email_status"] = "sent"
        except (OSError, smtplib.SMTPException, RuntimeError) as error:
            record["email_status"] = "failed"
            record["error"] = _append_error(
                record["error"], f"Email failed: {error}"
            )
            try:
                smtp_server.quit()
            except (OSError, smtplib.SMTPException):
                pass
            smtp_server = None

    if smtp_server is not None:
        try:
            smtp_server.quit()
        except (OSError, smtplib.SMTPException):
            pass

    _write_report(batch)
    return batch


def load_certificate_record(
    output_root: Path | str,
    certificate_uid: str,
) -> tuple[dict[str, str], Path]:
    """Resolve an unexpired certificate UID to its record and image."""
    if not CERTIFICATE_UID_PATTERN.fullmatch(certificate_uid):
        raise FileNotFoundError("Certificate UID was not found.")

    output_root = Path(output_root).resolve()
    record_path = output_root / "registry" / f"{certificate_uid}.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError("Certificate UID was not found.") from None
    except (OSError, json.JSONDecodeError) as error:
        raise OSError("Certificate record could not be read.") from error

    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.now().astimezone() >= expires_at:
        raise TimeoutError("This certificate verification link has expired.")

    certificate_path = (output_root / record["certificate_path"]).resolve()
    if not certificate_path.is_relative_to(output_root):
        raise OSError("Certificate record points outside the output directory.")
    if not certificate_path.is_file():
        raise FileNotFoundError("The certificate image is no longer available.")
    return record, certificate_path


def build_verification_url(
    certificate_uid: str,
    public_app_url: str | None,
) -> str:
    """Build the public app's bearer link; never substitute a local URL."""
    if public_app_url is None:
        return ""
    return f"{public_app_url.rstrip('/')}/?{urlencode({'c': certificate_uid})}"


def _save_certificate_record(
    output_root: Path,
    certificate_uid: str,
    name: str,
    expires_at: datetime,
    certificate_path: Path,
) -> None:
    registry_dir = output_root / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    registry_record = {
        "certificate_uid": certificate_uid,
        "name": name,
        "expires_at": expires_at.isoformat(timespec="seconds"),
        "certificate_path": certificate_path.resolve().relative_to(
            output_root
        ).as_posix(),
    }
    record_path = registry_dir / f"{certificate_uid}.json"
    temporary_path = record_path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(registry_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(record_path)


def _write_archive(
    archive_path: Path,
    certificate_paths: Iterable[Path],
) -> None:
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for certificate_path in certificate_paths:
            archive.write(certificate_path, certificate_path.name)


def _write_report(batch: PreviewBatch) -> None:
    pd.DataFrame(batch.records, columns=REPORT_COLUMNS).to_csv(
        batch.report_path,
        index=False,
        encoding="utf-8-sig",
    )


def _add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def _append_error(current: str, message: str) -> str:
    return f"{current}; {message}" if current else message
