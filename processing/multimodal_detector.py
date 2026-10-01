import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

from pdf_processor import extract_pdf_content

from detection.detection_pipeline import run_detection

from backend.risk_engine import calculate_risk


# ============================================================
# PDF SECURITY PROCESSING
# ============================================================

def process_pdf_for_security(pdf_path: str):

    # --------------------------------------------------------
    # STEP 1: Extract PDF content
    # --------------------------------------------------------

    pdf_result = extract_pdf_content(
        pdf_path
    )

    page_results = []

    all_findings = []

    # --------------------------------------------------------
    # STEP 2: Process each PDF page
    # --------------------------------------------------------

    for page in pdf_result["pages"]:

        page_text = page["text"]

        if not page_text:
            continue

        # ----------------------------------------------------
        # STEP 3: Run existing detection pipeline
        # ----------------------------------------------------

        findings = run_detection(
            page_text
        )

        page_findings = []

        # ----------------------------------------------------
        # STEP 4: Add provenance information
        # ----------------------------------------------------

        for finding in findings:

            enriched_finding = {
                **finding,

                "page_number":
                    page["page_number"],

                "source_document":
                    pdf_result["file_name"],

                "extraction_source":
                    (
                        "OCR"
                        if page["ocr_used"]
                        else "EMBEDDED_TEXT"
                    )
            }

            page_findings.append(
                enriched_finding
            )

            # ------------------------------------------------
            # Only the required fields go into risk engine
            # ------------------------------------------------

            risk_finding = {
                "type":
                    finding.get("type"),

                "confidence":
                    finding.get(
                        "confidence",
                        1.0
                    )
            }

            all_findings.append(
                risk_finding
            )

        # ----------------------------------------------------
        # Store page result
        # ----------------------------------------------------

        page_results.append({

            "page_number":
                page["page_number"],

            "source":
                (
                    "OCR"
                    if page["ocr_used"]
                    else "EMBEDDED_TEXT"
                ),

            "ocr_used":
                page["ocr_used"],

            "text":
                page_text,

            "findings":
                page_findings
        })

    # --------------------------------------------------------
    # STEP 5: Calculate risk
    # --------------------------------------------------------

    history = []

    risk_result = calculate_risk(
        all_findings,
        history
    )

    # --------------------------------------------------------
    # STEP 6: Return complete security result
    # --------------------------------------------------------

    return {

        "file_name":
            pdf_result["file_name"],

        "page_count":
            pdf_result["page_count"],

        "pages":
            page_results,

        "risk":
            risk_result
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_pdf = (
        "sample_data/"
        "synthetic_attacks/"
        "test_sensitive.pdf"
    )

    result = process_pdf_for_security(
        test_pdf
    )

    print()
    print(
        "PDF SECURITY RESULT"
    )
    print(
        "==================="
    )

    print(
        "File:",
        result["file_name"]
    )

    print(
        "Pages:",
        result["page_count"]
    )

    # --------------------------------------------------------
    # Display page findings
    # --------------------------------------------------------

    for page in result["pages"]:

        print()
        print(
            f"--- PAGE "
            f"{page['page_number']} ---"
        )

        print(
            "Extraction Source:",
            page["source"]
        )

        print(
            "OCR Used:",
            page["ocr_used"]
        )

        print()
        print(
            "Findings:"
        )

        if page["findings"]:

            for finding in page["findings"]:

                print(
                    {
                        "type":
                            finding.get(
                                "type"
                            ),

                        "source":
                            finding.get(
                                "source"
                            ),

                        "confidence":
                            finding.get(
                                "confidence"
                            ),

                        "page":
                            finding.get(
                                "page_number"
                            ),

                        "extraction":
                            finding.get(
                                "extraction_source"
                            )
                    }
                )

        else:

            print(
                "No findings."
            )

    # --------------------------------------------------------
    # Display risk
    # --------------------------------------------------------

    print()
    print(
        "RISK RESULT"
    )
    print(
        "==========="
    )

    print(
        result["risk"]
    )