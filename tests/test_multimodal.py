from pathlib import Path

from processing.pdf_processor import extract_pdf_content
from processing.docx_processor import extract_docx_content
from processing.xlsx_processor import extract_xlsx_content
from processing.pptx_processor import extract_pptx_content
from processing.image_processor import extract_image_content


BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_data" / "synthetic_attacks"


def find_sample_file(extension):
    files = list(SAMPLE_DIR.glob(f"*{extension}"))
    assert files, f"No sample file found for {extension}"
    return files[0]


def test_pdf_processor_extracts_content():
    pdf_path = find_sample_file(".pdf")

    result = extract_pdf_content(str(pdf_path))

    assert result["text"]
    assert result["page_count"] >= 1
    assert result["pages"]

    for page in result["pages"]:
        assert "page_number" in page
        assert "text" in page
        assert "extraction_source" in page


def test_pdf_processor_preserves_page_provenance():
    pdf_path = find_sample_file(".pdf")

    result = extract_pdf_content(str(pdf_path))

    sources = {
        page["extraction_source"]
        for page in result["pages"]
    }

    assert sources
    assert sources.issubset(
        {"EMBEDDED_TEXT", "OCR", "NONE"}
    )


def test_docx_processor_extracts_content():
    docx_path = find_sample_file(".docx")

    result = extract_docx_content(str(docx_path))

    assert result["text"]
    assert result["paragraph_count"] >= 1
    assert "source_segments" in result
    assert result["source_segments"]


def test_docx_processor_preserves_provenance():
    docx_path = find_sample_file(".docx")

    result = extract_docx_content(str(docx_path))

    for segment in result["source_segments"]:
        assert "start" in segment
        assert "end" in segment
        assert "location" in segment
        assert "source_type" in segment
        assert "source_id" in segment


def test_xlsx_processor_extracts_content():
    xlsx_path = find_sample_file(".xlsx")

    result = extract_xlsx_content(str(xlsx_path))

    assert result["text"]
    assert result["worksheet_count"] >= 1
    assert result["source_segments"]


def test_xlsx_processor_preserves_cell_provenance():
    xlsx_path = find_sample_file(".xlsx")

    result = extract_xlsx_content(str(xlsx_path))

    for segment in result["source_segments"]:
        assert "start" in segment
        assert "end" in segment
        assert "location" in segment
        assert segment["source_type"] == "XLSX_CELL"
        assert "sheet_name" in segment
        assert "cell" in segment


def test_pptx_processor_extracts_content():
    pptx_path = find_sample_file(".pptx")

    result = extract_pptx_content(str(pptx_path))

    assert result["text"]
    assert result["slide_count"] >= 1
    assert result["source_segments"]


def test_pptx_processor_preserves_slide_provenance():
    pptx_path = find_sample_file(".pptx")

    result = extract_pptx_content(str(pptx_path))

    for segment in result["source_segments"]:
        assert "start" in segment
        assert "end" in segment
        assert "location" in segment
        assert "source_type" in segment

        assert (
            "SLIDE" in segment["location"]
            or "SLIDE" in segment["source_type"]
        )


def test_image_processor_extracts_ocr_content():
    image_path = find_sample_file(".png")

    result = extract_image_content(str(image_path))

    assert result["text"]
    assert result["ocr_used"] is True
    assert result["ocr_engine"] == "Tesseract"


def test_image_processor_returns_metadata():
    image_path = find_sample_file(".png")

    result = extract_image_content(str(image_path))

    assert result["image_format"]
    assert result["width"] > 0
    assert result["height"] > 0
    assert result["source_segments"]


def test_all_modalities_produce_non_empty_text():
    pdf_result = extract_pdf_content(
        str(find_sample_file(".pdf"))
    )

    docx_result = extract_docx_content(
        str(find_sample_file(".docx"))
    )

    xlsx_result = extract_xlsx_content(
        str(find_sample_file(".xlsx"))
    )

    pptx_result = extract_pptx_content(
        str(find_sample_file(".pptx"))
    )

    image_result = extract_image_content(
        str(find_sample_file(".png"))
    )

    results = [
        pdf_result["text"],
        docx_result["text"],
        xlsx_result["text"],
        pptx_result["text"],
        image_result["text"],
    ]

    for text in results:
        assert text
        assert len(text.strip()) > 0