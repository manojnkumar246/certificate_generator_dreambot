from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from certificate_generator.personalize_template import personalize_certificate


class PersonalizeCertificateTests(unittest.TestCase):
    def test_renders_all_fields_to_jpeg_without_changing_dimensions(self) -> None:
        template_path = (
            Path(__file__).resolve().parent.parent / "inputs" / "template.png"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "certificate_output.jpg"

            result = personalize_certificate(
                template_path,
                output_path,
                certificate_number="DB-WS7-2026-001",
                student_name="John Doe",
                workshop_duration="22–24 July 2026",
                certificate_url=(
                    "verify.dreambot.co.in/cert/DB-WS7-2026-001"
                ),
            )

            self.assertEqual(result, output_path)
            self.assertTrue(output_path.is_file())
            with Image.open(output_path) as generated:
                self.assertEqual(generated.format, "JPEG")
                self.assertEqual(generated.size, (2450, 1728))

    def test_rejects_empty_dynamic_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            personalize_certificate(
                "unused-template.png",
                "unused-output.jpg",
                certificate_number="DB-001",
                student_name=" ",
                workshop_duration="22–24 July 2026",
                certificate_url="verify.example/cert/DB-001",
            )


if __name__ == "__main__":
    unittest.main()
