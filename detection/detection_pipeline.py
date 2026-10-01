from detection.basic_detector import detect_sensitive_data
from detection.presidio_detector import detect_with_presidio
from detection.custom_recognizers import detect_custom_entities
from detection.encoding_detector import decode_base64_candidates
from detection.canonicalizer import canonicalize_text


def _canonicalize_with_mapping(text: str):
    """
    Canonicalize text while preserving a mapping from
    canonical-text positions back to original-text positions.

    This allows detectors to operate on canonicalized text
    without breaking finding offsets used later by masking.
    """

    canonical_chars = []
    original_indices = []

    for index, character in enumerate(text):

        canonical_character = canonicalize_text(
            character
        )

        if canonical_character == "":
            continue

        for output_character in canonical_character:
            canonical_chars.append(
                output_character
            )
            original_indices.append(
                index
            )

    return (
        "".join(canonical_chars),
        original_indices
    )


def _map_span_to_original(
    start,
    end,
    index_map,
    original_length
):
    """
    Convert a detector span from canonical-text
    coordinates back to original-text coordinates.
    """

    if start is None or end is None:
        return start, end

    if start >= len(index_map):
        original_start = original_length
    else:
        original_start = index_map[start]

    if end <= 0:
        original_end = 0

    elif end - 1 < len(index_map):
        original_end = (
            index_map[end - 1] + 1
        )

    else:
        original_end = original_length

    return (
        original_start,
        original_end
    )


def run_detection(
    text: str,
    enable_canonicalization: bool = True
):
    """
    Run the unified Shadow AI detection pipeline.

    Parameters
    ----------
    text:
        Original user input.

    enable_canonicalization:
        True  -> V3 hardened pipeline.
        False -> V2 baseline pipeline.

    Returns
    -------
    list
        Unified detection findings.
    """

    findings = []

    # =====================================================
    # 0. Canonicalization
    #
    # V2 baseline:
    #     canonicalization disabled
    #
    # V3:
    #     conservative Unicode canonicalization enabled
    #
    # The index map ensures detector offsets can be
    # converted back to the original user input.
    # =====================================================

    if enable_canonicalization:

        canonical_text, index_map = (
            _canonicalize_with_mapping(
                text
            )
        )

    else:

        canonical_text = text

        index_map = list(
            range(len(text))
        )

    # =====================================================
    # 1. Basic regex detector
    # =====================================================

    basic_findings = detect_sensitive_data(
        canonical_text
    )

    for finding in basic_findings:

        start, end = _map_span_to_original(
            finding.get("start"),
            finding.get("end"),
            index_map,
            len(text)
        )

        findings.append({
            "source": "BASIC",
            "type": finding["type"],
            "severity": finding["severity"],
            "start": start,
            "end": end,
            "confidence": finding.get(
                "confidence",
                1.0
            )
        })

    # =====================================================
    # 2. Presidio detector
    # =====================================================

    presidio_findings = detect_with_presidio(
        canonical_text
    )

    for finding in presidio_findings:

        start, end = _map_span_to_original(
            finding["start"],
            finding["end"],
            index_map,
            len(text)
        )

        findings.append({
            "source": "PRESIDIO",
            "type": finding["type"],
            "start": start,
            "end": end,
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

    custom_findings = detect_custom_entities(
        canonical_text
    )

    for finding in custom_findings:

        start, end = _map_span_to_original(
            finding["start"],
            finding["end"],
            index_map,
            len(text)
        )

        findings.append({
            "source": "CUSTOM",
            "type": finding["type"],
            "start": start,
            "end": end,
            "score": finding["score"],
            "confidence": finding.get(
                "confidence",
                finding["score"]
            ),
            "value": finding["value"]
        })

    # =====================================================
    # 4. Base64 detection
    #
    # V1 Red-Team finding:
    # Sensitive values encoded with Base64 were missed.
    #
    # V2 mitigation:
    # Decode valid Base64 candidates and run the existing
    # detection pipeline against the decoded content.
    #
    # V3 continues to preserve this capability.
    # =====================================================

    base64_candidates = (
        decode_base64_candidates(
            canonical_text
        )
    )

    for candidate in base64_candidates:

        decoded_text = candidate[
            "decoded_value"
        ]

        # ---------------------------------------------
        # Map Base64 candidate span back to original
        # text.
        # ---------------------------------------------

        candidate_start, candidate_end = (
            _map_span_to_original(
                candidate["start"],
                candidate["end"],
                index_map,
                len(text)
            )
        )

        # ---------------------------------------------
        # Run existing detectors against decoded text.
        # ---------------------------------------------

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
        # Preserve decoded BASIC findings.
        # ---------------------------------------------

        for finding in decoded_basic:

            findings.append({
                "source": "BASE64_BASIC",
                "type": finding["type"],
                "severity": finding["severity"],
                "start": candidate_start,
                "end": candidate_end,
                "confidence": finding.get(
                    "confidence",
                    1.0
                ),
                "decoded_value": decoded_text
            })

        # ---------------------------------------------
        # Preserve decoded PRESIDIO findings.
        # ---------------------------------------------

        for finding in decoded_presidio:

            findings.append({
                "source": "BASE64_PRESIDIO",
                "type": finding["type"],
                "start": candidate_start,
                "end": candidate_end,
                "score": finding["score"],
                "confidence": finding.get(
                    "confidence",
                    finding["score"]
                ),
                "decoded_value": decoded_text
            })

        # ---------------------------------------------
        # Preserve decoded CUSTOM findings.
        # ---------------------------------------------

        for finding in decoded_custom:

            findings.append({
                "source": "BASE64_CUSTOM",
                "type": finding["type"],
                "start": candidate_start,
                "end": candidate_end,
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