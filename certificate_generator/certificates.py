from __future__ import annotations

import io
import re
import warnings
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def safe_filename(name: str) -> str:
    """Return a filesystem-safe name for a generated certificate."""
    normalized = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE).strip()
    normalized = re.sub(r"\s+", "_", normalized)
    return normalized or "student"


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a system TrueType font, falling back to Pillow's built-in font."""
    candidates = (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/times.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "arial.ttf",
        "times.ttf",
    )
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue

    warnings.warn(
        "No TrueType font was found; using Pillow's default font.",
        RuntimeWarning,
        stacklevel=2,
    )
    return ImageFont.load_default()


def generate_certificate(student_name: str, template_path: Path | str) -> io.BytesIO:
    """Draw a student's name on the template and return a JPEG buffer."""
    with Image.open(template_path) as source:
        template = source.convert("RGB")

    draw = ImageDraw.Draw(template)
    draw.text(
        (template.width // 2, 520),
        student_name,
        font=load_font(90),
        fill=(35, 75, 125),
        anchor="mm",
    )

    buffer = io.BytesIO()
    template.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)
    return buffer
