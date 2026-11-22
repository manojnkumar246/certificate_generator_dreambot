from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageStat import Stat


REFERENCE_SIZE = (2450, 1728)
FONT_CANDIDATES = {
    "sans": (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ),
    "sans_bold": (
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ),
    "sans_bold_condensed": (
        Path("C:/Windows/Fonts/ArialNovaCond-Bold.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
    ),
    "serif": (
        Path("C:/Windows/Fonts/georgia.ttf"),
        Path("/System/Library/Fonts/Supplemental/Georgia.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    ),
}

# Regions are measured against the supplied 2450 x 1728 template and scale
# proportionally for copies exported at another resolution.
PLACEHOLDER_REGIONS = {
    "certificate_number": (1765, 190, 2275, 245),
    "student_name": (850, 790, 1600, 890),
    "workshop_duration": (650, 1263, 1105, 1310),
    "certificate_url": (875, 1410, 1590, 1470),
}


def _scaled_box(
    box: tuple[int, int, int, int],
    image_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    scale_x = image_size[0] / REFERENCE_SIZE[0]
    scale_y = image_size[1] / REFERENCE_SIZE[1]
    return (
        round(box[0] * scale_x),
        round(box[1] * scale_y),
        round(box[2] * scale_x),
        round(box[3] * scale_y),
    )


def _font(family: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES[family]:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError(
        f"No system font was found for {family}: "
        + ", ".join(str(path) for path in FONT_CANDIDATES[family])
    )


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    family: str,
    preferred_size: int,
    minimum_size: int,
    max_width: int,
) -> ImageFont.FreeTypeFont:
    for size in range(preferred_size, minimum_size - 1, -1):
        candidate = _font(family, size)
        if draw.textbbox((0, 0), text, font=candidate)[2] <= max_width:
            return candidate
    raise ValueError(f"Text does not fit in its certificate area: {text!r}")


def _clear_region(
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    """Replace placeholder ink with a locally sampled, smoothly blended fill."""
    left, top, right, bottom = box
    height = bottom - top
    band = max(2, min(6, height // 10))
    top_color = Stat(image.crop((left, top - band, right, top))).mean
    bottom_color = Stat(image.crop((left, bottom, right, bottom + band))).mean
    draw = ImageDraw.Draw(image)

    for y in range(top, bottom):
        weight = (y - top + 0.5) / height
        color = tuple(
            round(
                top_color[channel] * (1 - weight)
                + bottom_color[channel] * weight
            )
            for channel in range(3)
        )
        draw.line((left, y, right - 1, y), fill=color)


def personalize_certificate(
    template_path: Path | str,
    output_path: Path | str,
    *,
    certificate_number: str,
    student_name: str,
    workshop_duration: str,
    certificate_url: str,
) -> Path:
    """Replace the template's four bracketed fields and save a JPG certificate."""
    if not all(
        value.strip()
        for value in (
            certificate_number,
            student_name,
            workshop_duration,
        )
    ):
        raise ValueError(
            "Certificate number, name, and duration must not be empty."
        )

    with Image.open(template_path) as source:
        image = source.convert("RGB")

    boxes = {
        key: _scaled_box(box, image.size)
        for key, box in PLACEHOLDER_REGIONS.items()
    }
    for box in boxes.values():
        left, top, right, bottom = box
        if (
            left < 6
            or top < 6
            or right + 6 > image.width
            or bottom + 6 > image.height
        ):
            raise ValueError(
                "The template is too small for the measured placeholder layout."
            )
        _clear_region(image, box)

    scale = image.width / REFERENCE_SIZE[0]
    draw = ImageDraw.Draw(image)

    number_box = boxes["certificate_number"]
    number = certificate_number.strip()
    number_font = _fit_font(
        draw,
        number,
        "sans_bold_condensed",
        round(42 * scale),
        round(20 * scale),
        round(number_box[2] - number_box[0] - 18 * scale),
    )
    draw.text(
        (number_box[2] - round(8 * scale), (number_box[1] + number_box[3]) // 2),
        number,
        font=number_font,
        fill=(20, 20, 20),
        anchor="rm",
    )

    name_box = boxes["student_name"]
    name_font = _fit_font(
        draw,
        student_name.strip(),
        "sans_bold",
        round(96 * scale),
        round(36 * scale),
        name_box[2] - name_box[0] - round(24 * scale),
    )
    draw.text(
        ((name_box[0] + name_box[2]) // 2, (name_box[1] + name_box[3]) // 2),
        student_name.strip(),
        font=name_font,
        fill=(24, 24, 27),
        anchor="mm",
    )

    duration_box = boxes["workshop_duration"]
    duration_font = _fit_font(
        draw,
        workshop_duration.strip(),
        "serif",
        round(32 * scale),
        round(20 * scale),
        duration_box[2] - duration_box[0] - round(12 * scale),
    )
    draw.text(
        (
            duration_box[0] + round(10 * scale),
            (duration_box[1] + duration_box[3]) // 2,
        ),
        workshop_duration.strip(),
        font=duration_font,
        fill=(28, 28, 28),
        anchor="lm",
    )

    url_box = boxes["certificate_url"]
    if certificate_url.strip():
        url_parts = urlsplit(certificate_url.strip())
        query = parse_qs(url_parts.query)
        certificate_uid = query.get("c", [""])[0]
        printable_url = f"{url_parts.scheme}://{url_parts.netloc}{url_parts.path}"
        if url_parts.query:
            printable_url = f"{printable_url}?{url_parts.query}"
        elif certificate_uid:
            printable_url = f"{printable_url}?c={certificate_uid}"
        verification_text = f"Verify certificate at: {printable_url}"
    else:
        verification_text = "Recipient verification link not configured"

    url_font = _fit_font(
        draw,
        verification_text,
        "serif",
        round(24 * scale),
        round(8 * scale),
        url_box[2] - url_box[0] - round(16 * scale),
    )
    draw.text(
        ((url_box[0] + url_box[2]) // 2, (url_box[1] + url_box[3]) // 2),
        verification_text,
        font=url_font,
        fill=(28, 28, 28),
        anchor="mm",
    )

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="JPEG", quality=95, optimize=True)
    return destination


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description=(
            "Generate one personalized JPG certificate from the supplied template."
        )
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=project_root / "inputs" / "template.png",
        help="Template image path (default: inputs/template.png).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "certificate_output.jpg",
        help="JPG output path (default: certificate_output.jpg).",
    )
    parser.add_argument("--student-name", default="John Doe")
    parser.add_argument("--workshop-duration", default="22–24 July 2026")
    arguments = parser.parse_args()

    import pandas as pd

    from certificate_generator.processing import generate_previews

    batch = generate_previews(
        students=pd.DataFrame(
            [
                {
                    "Name": arguments.student_name,
                    "Email": "",
                    "Send": "no",
                    "Duration": arguments.workshop_duration,
                }
            ]
        ),
        template_path=arguments.template,
        output_root=project_root / "outputs",
    )
    record = batch.records[0]
    if record["certificate_status"] != "generated":
        raise RuntimeError(record["error"])

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(batch.certificate_paths[record["certificate_uid"]], arguments.output)
    print(f"Certificate saved: {arguments.output}")
    print(f"Certificate UID: {record['certificate_uid']}")
    print(f"Verification URL: {record['verification_url']}")
    print(f"Expires: {record['expires_at']}")


if __name__ == "__main__":
    main()
