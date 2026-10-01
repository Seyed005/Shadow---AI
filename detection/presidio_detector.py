from presidio_analyzer import AnalyzerEngine


# =========================================================
# PRESIDIO ANALYZER
# =========================================================

analyzer = AnalyzerEngine()


# =========================================================
# CONFIGURATION
# =========================================================

# Minimum confidence required for a Presidio finding
# to enter the Shadow AI detection pipeline.
MIN_CONFIDENCE = 0.50


# Entity types that are useful for the current
# Shadow AI security pipeline.
ALLOWED_ENTITIES = {
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IP_ADDRESS",
    "CREDIT_CARD",
    "DATE_TIME",
    "LOCATION",
    "URL"
}


# =========================================================
# PRESIDIO DETECTION
# =========================================================

def detect_with_presidio(text: str):
    """
    Detect supported PII entities using Microsoft Presidio.

    Low-confidence findings are filtered so that weak
    Presidio guesses do not unnecessarily increase the
    Shadow AI risk score.

    Custom security entities such as PASSWORD,
    EMPLOYEE_ID and API_KEY_LIKE are handled separately
    by the project's custom/basic detectors.
    """

    if not text or not text.strip():
        return []

    results = analyzer.analyze(
        text=text,
        language="en"
    )

    findings = []

    for result in results:

        entity_type = result.entity_type
        score = round(result.score, 2)

        # -------------------------------------------------
        # ENTITY FILTER
        # -------------------------------------------------

        if entity_type not in ALLOWED_ENTITIES:
            continue

        # -------------------------------------------------
        # CONFIDENCE FILTER
        # -------------------------------------------------

        if score < MIN_CONFIDENCE:
            continue

        # -------------------------------------------------
        # FINDING
        # -------------------------------------------------

        findings.append({
            "type": entity_type,
            "start": result.start,
            "end": result.end,
            "score": score,
            "value": text[result.start:result.end]
        })

    # -----------------------------------------------------
    # REMOVE PHONE FINDINGS THAT OVERLAP IP ADDRESSES
    # -----------------------------------------------------

    ip_ranges = [
        (finding["start"], finding["end"])
        for finding in findings
        if finding["type"] == "IP_ADDRESS"
    ]

    filtered_findings = []

    for finding in findings:

        if finding["type"] == "PHONE_NUMBER":

            overlaps_ip = any(
                finding["start"] < ip_end
                and finding["end"] > ip_start
                for ip_start, ip_end in ip_ranges
            )

            if overlaps_ip:
                continue

        filtered_findings.append(finding)

    return filtered_findings


# =========================================================
# LOCAL TEST
# =========================================================

if __name__ == "__main__":

    test_text = """
    My name is John.
    My email is john@example.com.
    My phone number is 9876543210.
    My IP address is 192.168.1.10.
    """

    results = detect_with_presidio(test_text)

    print("Presidio Detection Results:")

    for result in results:
        print(result)