from pathlib import Path

from PIL import Image, ImageOps
import pytesseract


# Use the same Tesseract installation already verified
# for the Shadow AI PDF OCR pipeline.
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


def extract_image_content(image_path: str) -> dict:
    """
    Extract text from an image using Tesseract OCR.

    The returned text is compatible with the existing
    Shadow AI detection pipeline.

    Character-level provenance is preserved so that
    future findings can be traced back to the image
    source.
    """

    image_file = Path(image_path)

    if not image_file.exists():
        raise FileNotFoundError(
            f"Image file not found: {image_file}"
        )

    if image_file.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(
            "Unsupported image format. "
            "Supported formats: PNG, JPG, JPEG, BMP, "
            "TIF, TIFF, WEBP."
        )

    image = Image.open(image_path)

    # Convert to RGB so Tesseract receives a consistent image mode.
    image = image.convert("RGB")

    # Grayscale improves OCR consistency for many document images.
    grayscale = ImageOps.grayscale(image)

    # OCR configuration:
    # PSM 6 assumes a block of text, which is suitable for
    # synthetic security-document images used in V1 testing.
    ocr_text = pytesseract.image_to_string(
        grayscale,
        config="--psm 6"
    ).strip()

    # Preserve the exact OCR text as the canonical representation.
    canonical_text = ocr_text

    source_segments = []

    if canonical_text:
        source_segments.append({
            "start": 0,
            "end": len(canonical_text),
            "location": "IMAGE OCR",
            "source_type": "IMAGE_OCR",
            "source_id": image_file.name,
        })

    return {
        "file_name": image_file.name,
        "image_format": image_file.suffix.lower(),
        "width": image.width,
        "height": image.height,
        "text": canonical_text,
        "ocr_used": True,
        "ocr_engine": "Tesseract",
        "source_segments": source_segments,
    }