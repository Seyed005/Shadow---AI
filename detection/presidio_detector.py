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
    # AND REMOVE URL FINDINGS THAT OVERLAP EMAIL ADDRESSES
    # OR ARE NOT LEGITIMATE STANDALONE URLS
    # -----------------------------------------------------

    import re

    ip_ranges = [
        (finding["start"], finding["end"])
        for finding in findings
        if finding["type"] == "IP_ADDRESS"
    ]

    email_pattern = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )
    email_ranges = [
        (m.start(), m.end())
        for m in email_pattern.finditer(text)
    ]
    for finding in findings:
        if finding["type"] == "EMAIL_ADDRESS":
            email_ranges.append((finding["start"], finding["end"]))

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

        if finding["type"] == "URL":

            start = finding["start"]
            end = finding["end"]

            # Filter out URL if it overlaps any email address
            overlaps_email = any(
                start < ee and end > es
                for es, ee in email_ranges
            )
            if overlaps_email:
                continue

            # Filter out if preceded by @ or part of an email address
            if start > 0 and (text[start - 1] == "@" or text[start - 1].isalnum() or text[start - 1] in "._"):
                continue

            # Filter out if followed by alphanumeric characters without boundary
            if end < len(text) and text[end].isalnum():
                continue

            # Verify legitimate URL structure
            val_lower = finding["value"].lower().strip()
            if not val_lower.startswith(("http://", "https://", "www.")):
                if "." not in val_lower:
                    continue
                parts = val_lower.split("/")[0].split(".")
                tld = parts[-1]
                file_exts = {
                    "pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt",
                    "png", "jpg", "jpeg", "bmp", "gif", "zip", "tar", "gz",
                    "py", "js", "html", "css", "json", "xml", "md", "do", "cx"
                }
                if tld in file_exts:
                    continue
                known_web_tlds = {
                    "com", "org", "net", "edu", "gov", "io", "ai", "dev",
                    "app", "co", "uk", "xyz", "info", "biz", "me", "tv",
                    "online", "site", "top", "live", "club", "pro", "security"
                }
                if tld not in known_web_tlds:
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
