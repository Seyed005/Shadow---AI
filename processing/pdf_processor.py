import io
from pathlib import Path

import pymupdf
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# CONFIGURATION
# ============================================================

MIN_TEXT_LENGTH_FOR_OCR = 40
OCR_SCALE = 2


# ============================================================
# PDF PROCESSOR
# ============================================================

def extract_pdf_content(pdf_path: str):

    pdf_file = Path(pdf_path)

    # --------------------------------------------------------
    # Validate file existence
    # --------------------------------------------------------

    if not pdf_file.exists():

        raise FileNotFoundError(
            f"PDF file not found: {pdf_file}"
        )

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    if pdf_file.suffix.lower() != ".pdf":

        raise ValueError(
            "Input file must be a PDF."
        )

    # --------------------------------------------------------
    # Open PDF
    # --------------------------------------------------------

    document = pymupdf.open(
        pdf_path
    )

    pages = []
    total_text = ""

    # --------------------------------------------------------
    # Process every page
    # --------------------------------------------------------

    for page_number, page in enumerate(
        document,
        start=1
    ):

        # ----------------------------------------------------
        # 1. Extract embedded PDF text
        # ----------------------------------------------------

        embedded_text = page.get_text(
            "text"
        ).strip()

        ocr_text = ""
        ocr_used = False

        # ----------------------------------------------------
        # 2. Use OCR when embedded text is insufficient
        # ----------------------------------------------------

        if len(embedded_text) < MIN_TEXT_LENGTH_FOR_OCR:

            try:

                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(
                        OCR_SCALE,
                        OCR_SCALE
                    ),
                    alpha=False
                )

                image_bytes = pixmap.tobytes(
                    "png"
                )

                image = Image.open(
                    io.BytesIO(image_bytes)
                )

                ocr_text = (
                    pytesseract
                    .image_to_string(image)
                    .strip()
                )

                if ocr_text:

                    ocr_used = True

            except Exception as error:

                print(
                    f"OCR failed on page "
                    f"{page_number}: {error}"
                )

        # ----------------------------------------------------
        # 3. Select final page representation
        # ----------------------------------------------------

        if embedded_text:

            page_text = embedded_text

            extraction_source = (
                "EMBEDDED_TEXT"
            )

        elif ocr_text:

            page_text = ocr_text

            extraction_source = (
                "OCR"
            )

        else:

            page_text = ""

            extraction_source = (
                "NONE"
            )

        # ----------------------------------------------------
        # 4. Add page text to complete document text
        # ----------------------------------------------------

        total_text += (

            f"\n--- PAGE {page_number} ---\n"
            f"{page_text}\n"

        )

        # ----------------------------------------------------
        # 5. Store page-level information
        # ----------------------------------------------------

        pages.append({

            "page_number":
                page_number,

            "text":
                page_text,

            "embedded_text_length":
                len(embedded_text),

            "ocr_used":
                ocr_used,

            "ocr_text_length":
                len(ocr_text),

            "extraction_source":
                extraction_source

        })

    # --------------------------------------------------------
    # 6. Extract PDF metadata
    # --------------------------------------------------------

    metadata = document.metadata

    page_count = len(document)

    # --------------------------------------------------------
    # 7. Build final result
    # --------------------------------------------------------

    result = {

        "file_name":
            pdf_file.name,

        "page_count":
            page_count,

        "metadata":
            metadata,

        "text":
            total_text.strip(),

        "pages":
            pages

    }

    # --------------------------------------------------------
    # 8. Close PDF
    # --------------------------------------------------------

    document.close()

    return result


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_pdf = (

        "sample_data/"
        "synthetic_attacks/"
        "test_sensitive.pdf"

    )

    try:

        result = extract_pdf_content(
            test_pdf
        )

        print(
            "\nPDF PROCESSING RESULT"
        )

        print(
            "====================="
        )

        print(
            "File:",
            result["file_name"]
        )

        print(
            "Pages:",
            result["page_count"]
        )

        print(
            "Total extracted characters:",
            len(result["text"])
        )

        print(
            "\nPage Information:"
        )

        for page in result["pages"]:

            print(

                f"Page {page['page_number']}: "
                f"text={page['embedded_text_length']} "
                f"OCR={page['ocr_used']} "
                f"OCR_text={page['ocr_text_length']} "
                f"Source={page['extraction_source']}"

            )

        print(
            "\nExtracted Text:"
        )

        print(
            result["text"]
        )

    except Exception as error:

        print(
            "\nPDF PROCESSING ERROR"
        )

        print(
            "===================="
        )

        print(
            error
        )