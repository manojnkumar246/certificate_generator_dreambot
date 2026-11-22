from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from certificate_generator import settings


class SmtpSettingsTests(unittest.TestCase):
    def test_reads_password_from_environment_without_displaying_it(self) -> None:
        with (
            patch.dict(os.environ, {"APP_PASSWORD": " test-password "}),
            patch("certificate_generator.settings.load_dotenv") as load_dotenv,
        ):
            password = settings.get_smtp_app_password()

        self.assertEqual(password, "test-password")
        load_dotenv.assert_called_once_with(
            dotenv_path=settings.ENV_FILE,
            override=False,
        )

    def test_reads_public_url_and_admin_password_from_environment(self) -> None:
        with (
            patch.dict(
                os.environ,
                {
                    "APP_PUBLIC_URL": "https://certificates.example.com/",
                    "APP_ADMIN_PASSWORD": "private-admin-password",
                },
            ),
            patch("certificate_generator.settings.load_dotenv"),
        ):
            self.assertEqual(
                settings.get_public_app_url(),
                "https://certificates.example.com",
            )
            self.assertEqual(
                settings.get_app_admin_password(),
                "private-admin-password",
            )

    def test_public_url_must_be_https_and_nonlocal(self) -> None:
        for value in ("http://example.com", "https://localhost:8501"):
            with (
                self.subTest(value=value),
                patch.dict(os.environ, {"APP_PUBLIC_URL": value}),
                patch("certificate_generator.settings.load_dotenv"),
            ):
                with self.assertRaises(ValueError):
                    settings.get_public_app_url()

if __name__ == "__main__":
    unittest.main()
