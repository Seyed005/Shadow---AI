from detection.basic_detector import detect_sensitive_data
from detection.presidio_detector import detect_with_presidio
from detection.custom_recognizers import detect_custom_entities
from detection.encoding_detector import decode_base64_candidates


def run_detection(text: str):
    findings = []

    # =====================================================
    # 1. Basic regex detector
    # =====================================================

    basic_findings = detect_sensitive_data(text)

    for finding in basic_findings:
        findings.append({
            "source": "BASIC",
            "type": finding["type"],
            "severity": finding["severity"],
            "start": finding.get("start"),
            "end": finding.get("end"),
            "confidence": finding.get(
                "confidence",
                1.0
            )
        })

    # =====================================================
    # 2. Presidio detector
    # =====================================================

    presidio_findings = detect_with_presidio(text)

    for finding in presidio_findings:
        findings.append({
            "source": "PRESIDIO",
            "type": finding["type"],
            "start": finding["start"],
            "end": finding["end"],
            "score": finding["score"],
            "confidence": finding.get(
                "confidence",
                finding["score"]
            ),
            "value": finding["value"]
        })

    # =====================================================
    # 3. Custom recognizers
    # =====================================================

    custom_findings = detect_custom_entities(text)

    for finding in custom_findings:
        findings.append({
            "source": "CUSTOM",
            "type": finding["type"],
            "start": finding["start"],
            "end": finding["end"],
            "score": finding["score"],
            "confidence": finding.get(
                "confidence",
                finding["score"]
            ),
            "value": finding["value"]
        })

    # =====================================================
    # 4. Base64 canonicalization detector
    #
    # Red Team finding from V1:
    # Sensitive values encoded with Base64 were missed.
    #
    # We decode valid Base64 candidates and run the
    # EXISTING detection pipeline on the decoded content.
    # =====================================================

    base64_candidates = (
        decode_base64_candidates(text)
    )

    for candidate in base64_candidates:

        decoded_text = candidate[
            "decoded_value"
        ]

        # Run existing detectors against decoded content.
        decoded_basic = detect_sensitive_data(
            decoded_text
        )

        decoded_presidio = detect_with_presidio(
            decoded_text
        )

        decoded_custom = detect_custom_entities(
            decoded_text
        )

        # ---------------------------------------------
        # Preserve decoded findings as Base64-derived
        # findings.
        # ---------------------------------------------

        for finding in decoded_basic:

            findings.append({
                "source": "BASE64_BASIC",
                "type": finding["type"],
                "severity": finding["severity"],
                "start": candidate["start"],
                "end": candidate["end"],
                "confidence": finding.get(
                    "confidence",
                    1.0
                ),
                "decoded_value": decoded_text
            })

        for finding in decoded_presidio:

            findings.append({
                "source": "BASE64_PRESIDIO",
                "type": finding["type"],
                "start": candidate["start"],
                "end": candidate["end"],
                "score": finding["score"],
                "confidence": finding.get(
                    "confidence",
                    finding["score"]
                ),
                "decoded_value": decoded_text
            })

        for finding in decoded_custom:

            findings.append({
                "source": "BASE64_CUSTOM",
                "type": finding["type"],
                "start": candidate["start"],
                "end": candidate["end"],
                "score": finding["score"],
                "confidence": finding.get(
                    "confidence",
                    finding["score"]
                ),
                "decoded_value": decoded_text
            })

    return findings


if __name__ == "__main__":

    test_text = """
    Employee ID: EMP-2026-0042
    My name is John.
    Email: john@example.com
    Phone: 9876543210
    Server: 192.168.1.10
    API Key: DEMO_API_KEY_12345
    Password: DemoPass123
    """

    results = run_detection(
        test_text
    )

    print(
        "Unified Detection Results:"
    )

    for result in results:
        print(result)