from typing import List, Dict


SEMANTIC_REPLACEMENTS = {
    "PERSON": "[SYNTHETIC_PERSON]",
    "EMAIL": "analyst@example.com",
    "EMAIL_ADDRESS": "analyst@example.com",
    "PHONE": "[SYNTHETIC_PHONE]",
    "PHONE_NUMBER": "[SYNTHETIC_PHONE]",
    "IP_ADDRESS": "192.0.2.10",
    "EMPLOYEE_ID": "[SYNTHETIC_EMPLOYEE_ID]",
    "PASSWORD": "[SYNTHETIC_PASSWORD]",
    "API_KEY_LIKE": "[SYNTHETIC_API_KEY]",
    "CREDIT_CARD": "[SYNTHETIC_CARD_NUMBER]",
    "DATABASE_CREDENTIAL": "[SYNTHETIC_DATABASE_CREDENTIAL]",
    "URL": "https://example.com",
    "LOCATION": "[SYNTHETIC_LOCATION]",
    "DATE_TIME": "[SYNTHETIC_DATE_TIME]",
}


# Higher priority means that the finding is preferred
# when two findings overlap.
SOURCE_PRIORITY = {
    "CUSTOM": 4,
    "BASIC+PRESIDIO": 3,
    "BASIC": 2,
    "PRESIDIO": 1,
}


def get_replacement(entity_type: str) -> str:
    """
    Return the semantic replacement for a detected
    sensitive entity.
    """

    return SEMANTIC_REPLACEMENTS.get(
        entity_type,
        f"[SYNTHETIC_{entity_type}]"
    )


def get_source_priority(finding: Dict) -> int:
    """
    Determine the priority of a finding source.
    """

    source = finding.get("source", "").upper()

    if "CUSTOM" in source:
        return SOURCE_PRIORITY["CUSTOM"]

    if "BASIC+PRESIDIO" in source:
        return SOURCE_PRIORITY["BASIC+PRESIDIO"]

    if "BASIC" in source:
        return SOURCE_PRIORITY["BASIC"]

    if "PRESIDIO" in source:
        return SOURCE_PRIORITY["PRESIDIO"]

    return 0


def select_non_overlapping_findings(
    findings: List[Dict]
) -> List[Dict]:
    """
    Select a clean set of non-overlapping findings.

    When findings overlap, prefer:
    1. Higher-confidence detection
    2. Higher-priority detection source
    3. Longer span

    This prevents overlapping entities such as:

        EMAIL      49-69
        URL        58-69

    from corrupting the sanitized text.
    """

    valid_findings = []

    for finding in findings:

        start = finding.get("start")
        end = finding.get("end")

        if start is None or end is None:
            continue

        if start < 0:
            continue

        if end <= start:
            continue

        valid_findings.append(finding)

    # Highest-quality candidates first.
    valid_findings.sort(
        key=lambda finding: (
            float(finding.get("confidence", 0.0)),
            get_source_priority(finding),
            finding["end"] - finding["start"]
        ),
        reverse=True
    )

    selected = []

    for candidate in valid_findings:

        candidate_start = candidate["start"]
        candidate_end = candidate["end"]

        overlaps = False

        for existing in selected:

            existing_start = existing["start"]
            existing_end = existing["end"]

            if (
                candidate_start < existing_end
                and candidate_end > existing_start
            ):
                overlaps = True
                break

        if not overlaps:
            selected.append(candidate)

    # Return findings in normal text order.
    selected.sort(
        key=lambda finding: (
            finding["start"],
            finding["end"]
        )
    )

    return selected


def mask_sensitive_data(
    text: str,
    findings: List[Dict]
) -> str:
    """
    Replace detected sensitive entities with
    semantic synthetic values.

    Replacements are applied from right to left
    after overlapping findings have been removed.
    """

    if not text:
        return text

    if not findings:
        return text

    selected_findings = select_non_overlapping_findings(
        findings
    )

    sanitized_text = text

    # Reverse order prevents earlier replacements
    # from changing the positions of later findings.
    selected_findings.sort(
        key=lambda finding: (
            finding["start"],
            finding["end"]
        ),
        reverse=True
    )

    for finding in selected_findings:

        start = finding["start"]
        end = finding["end"]

        entity_type = finding.get(
            "type",
            "SENSITIVE_DATA"
        )

        replacement = get_replacement(
            entity_type
        )

        sanitized_text = (
            sanitized_text[:start]
            + replacement
            + sanitized_text[end:]
        )

    return sanitized_text


def build_sanitization_preview(
    original_text: str,
    findings: List[Dict]
) -> Dict:
    """
    Build the Original vs Sanitized preview
    used by the Shadow AI interface.
    """

    sanitized_text = mask_sensitive_data(
        original_text,
        findings
    )

    return {
        "original_text": original_text,
        "sanitized_text": sanitized_text,
        "changed": (
            original_text != sanitized_text
        ),
        "finding_count": len(findings)
    }