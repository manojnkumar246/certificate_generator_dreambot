from __future__ import annotations

import tempfile
import unittest
import calendar
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd

from certificate_generator.processing import (
    CERTIFICATE_UID_PATTERN,
    normalize_student_columns,
    generate_previews,
    load_certificate_record,
    send_approved_emails,
)


class NormalizeStudentColumnsTests(unittest.TestCase):
    def test_normalizes_aliases_and_case(self) -> None:
        students = pd.DataFrame(
            {
                " student_name ": ["Alex"],
                "STUDENT_EMAIL": ["alex@example.com"],
                "send_email": ["yes"],
                "Workshop Duration": ["22–24 July 2026"],
            }
        )

        normalized = normalize_student_columns(students)

        self.assertEqual(
            list(normalized.columns),
            ["Name", "Email", "Send", "Duration"],
        )

    def test_rejects_missing_required_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            normalize_student_columns(pd.DataFrame({"Name": ["Alex"]}))


class ProcessStudentsTests(unittest.TestCase):
    def test_generates_unique_preview_uids_and_persists_expiring_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            template_path = (
                Path(__file__).resolve().parent.parent / "inputs" / "template.png"
            )
            students = pd.DataFrame(
                {
                    "Name": ["Alex Example", "Jamie Example"],
                    "Email": ["alex@example.com", "jamie@example.com"],
                    "Send": ["yes", "no"],
                    "Duration": ["1–3 August 2026", "5–6 August 2026"],
                }
            )

            with (
                patch(
                    "certificate_generator.processing.get_public_app_url",
                    return_value="https://certificates.example.com",
                ),
                patch("certificate_generator.processing.connect_smtp") as connect,
            ):
                before = datetime.now().astimezone()
                batch = generate_previews(
                    students=students,
                    template_path=template_path,
                    output_root=root / "outputs",
                )

            connect.assert_not_called()
            self.assertEqual(batch.generated_count, 2)
            self.assertEqual(batch.records[0]["duration"], "1–3 August 2026")
            self.assertEqual(batch.records[1]["duration"], "5–6 August 2026")
            self.assertTrue(batch.has_public_url)
            uids = [record["certificate_uid"] for record in batch.records]
            self.assertEqual(len(set(uids)), len(uids))
            self.assertTrue(all(CERTIFICATE_UID_PATTERN.fullmatch(uid) for uid in uids))
            self.assertEqual(
                batch.records[0]["verification_url"],
                f"https://certificates.example.com/?c={uids[0]}",
            )
            self.assertEqual(
                batch.records[1]["verification_url"],
                f"https://certificates.example.com/?c={uids[1]}",
            )
            self.assertEqual(
                [record["email_status"] for record in batch.records],
                ["pending_approval", "skipped"],
            )
            self.assertTrue(batch.report_path.is_file())
            self.assertTrue(batch.archive_path.is_file())

            expires_at = datetime.fromisoformat(batch.records[0]["expires_at"])
            self.assertEqual(
                expires_at,
                _add_six_months(before).replace(microsecond=0),
            )
            record, certificate_path = load_certificate_record(
                batch.output_root,
                uids[0],
            )
            self.assertEqual(record["certificate_uid"], uids[0])
            self.assertTrue(certificate_path.is_file())

            report = pd.read_csv(batch.report_path)
            self.assertEqual(report.loc[0, "duration"], "1–3 August 2026")
            self.assertEqual(report.loc[0, "email"], "alex@example.com")
            self.assertEqual(report.loc[0, "email_status"], "pending_approval")
            self.assertEqual(report.loc[1, "email_status"], "skipped")

    def test_email_is_sent_only_after_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            template_path = (
                Path(__file__).resolve().parent.parent / "inputs" / "template.png"
            )
            students = pd.DataFrame(
                {
                    "Name": ["Alex Example"],
                    "Email": ["alex@example.com"],
                    "Send": ["yes"],
                    "Duration": ["1–3 August 2026"],
                }
            )
            smtp = Mock()

            with (
                patch(
                    "certificate_generator.processing.get_public_app_url",
                    return_value="https://certificates.example.com",
                ),
            ):
                batch = generate_previews(
                    students,
                    template_path,
                    root / "outputs",
                )

            self.assertEqual(batch.emailed_count, 0)
            self.assertEqual(batch.records[0]["email_status"], "pending_approval")
            with (
                patch(
                    "certificate_generator.processing.connect_smtp",
                    return_value=smtp,
                ),
                patch("certificate_generator.processing.send_email") as send_email,
            ):
                send_approved_emails(
                    batch,
                    sender_email="sender@example.com",
                    email_password="not-a-real-password",
                )

            self.assertEqual(batch.emailed_count, 1)
            self.assertEqual(batch.records[0]["email_status"], "sent")
            send_email.assert_called_once()
            self.assertEqual(
                send_email.call_args.kwargs["verification_url"],
                batch.records[0]["verification_url"],
            )
            smtp.quit.assert_called_once()

    def test_sending_is_blocked_without_public_app_url(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            template_path = (
                Path(__file__).resolve().parent.parent / "inputs" / "template.png"
            )
            students = pd.DataFrame(
                {
                    "Name": ["Alex"],
                    "Email": ["alex@example.com"],
                    "Send": ["yes"],
                    "Duration": ["22–24 July 2026"],
                }
            )
            with patch(
                "certificate_generator.processing.get_public_app_url",
                return_value=None,
            ):
                batch = generate_previews(
                    students,
                    template_path,
                    root / "outputs",
                )

            self.assertEqual(batch.records[0]["verification_url"], "")
            self.assertFalse(batch.has_public_url)
            with self.assertRaisesRegex(ValueError, "APP_PUBLIC_URL"):
                send_approved_emails(batch, "sender@example.com", "fake-password")

    def test_expired_verification_link_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            template_path = (
                Path(__file__).resolve().parent.parent / "inputs" / "template.png"
            )
            students = pd.DataFrame(
                {
                    "Name": ["Alex"],
                    "Email": ["alex@example.com"],
                    "Send": ["no"],
                    "Duration": ["22–24 July 2026"],
                }
            )
            with patch(
                "certificate_generator.processing.get_public_app_url",
                return_value=None,
            ):
                batch = generate_previews(
                    students,
                    template_path,
                    root / "outputs",
                )

            uid = batch.records[0]["certificate_uid"]
            registry_path = batch.output_root / "registry" / f"{uid}.json"
            registry_record = json.loads(registry_path.read_text(encoding="utf-8"))
            registry_record["expires_at"] = "2000-01-01T00:00:00+00:00"
            registry_path.write_text(
                json.dumps(registry_record),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(TimeoutError, "expired"):
                load_certificate_record(batch.output_root, uid)

    def test_invalid_recipient_is_reported_without_connecting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            template_path = (
                Path(__file__).resolve().parent.parent / "inputs" / "template.png"
            )
            students = pd.DataFrame(
                {
                    "Name": ["Alex"],
                    "Email": ["not-an-email"],
                    "Send": ["yes"],
                    "Duration": ["22–24 July 2026"],
                }
            )

            with patch(
                "certificate_generator.processing.get_public_app_url",
                return_value="https://certificates.example.com",
            ):
                batch = generate_previews(
                    students,
                    template_path,
                    root / "outputs",
                )
            with (
                patch(
                    "certificate_generator.processing.connect_smtp",
                    return_value=Mock(),
                ) as connect,
            ):
                send_approved_emails(
                    batch,
                    "sender@example.com",
                    "not-a-real-password",
                )

            connect.assert_not_called()
            self.assertEqual(batch.error_count, 1)
            self.assertEqual(batch.records[0]["email_status"], "failed")
            self.assertIn("Invalid email address", batch.records[0]["error"])


def _add_six_months(value: datetime) -> datetime:
    month = (value.month + 5) % 12 + 1
    year = value.year + (value.month + 5) // 12
    return value.replace(
        year=year,
        month=month,
        day=min(value.day, calendar.monthrange(year, month)[1]),
    )


if __name__ == "__main__":
    unittest.main()
