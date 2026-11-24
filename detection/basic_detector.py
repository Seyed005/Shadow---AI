import re


def detect_sensitive_data(text: str):
    """
    Basic regex-based sensitive data detector.

    Detects every occurrence of supported patterns,
    rather than stopping at the first match.

    Designed to work with both natural text and
    canonicalized document content.
    """

    findings = []

    # ---------------------------------------------------------
    # EMAIL ADDRESS
    # ---------------------------------------------------------

    email_pattern = (
        r"\b[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    for match in re.finditer(
        email_pattern,
        text
    ):
        findings.append({
            "type": "EMAIL",
            "severity": "MEDIUM",
            "confidence": 1.0,
            "start": match.start(),
            "end": match.end()
        })

    # ---------------------------------------------------------
    # IPv4 ADDRESS
    # ---------------------------------------------------------

    ip_pattern = (
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    )

    for match in re.finditer(
        ip_pattern,
        text
    ):
        findings.append({
            "type": "IP_ADDRESS",
            "severity": "HIGH",
            "confidence": 1.0,
            "start": match.start(),
            "end": match.end()
        })

    # ---------------------------------------------------------
    # PASSWORD
    # ---------------------------------------------------------
    #
    # Supports:
    #
    # Password: DemoPass123
    # Password = DemoPass123
    #
    # and canonical document layouts:
    #
    # Password
    # DemoPass123
    #
    # The second form is limited to a nearby next line so
    # unrelated later text is not accidentally classified
    # as a password.
    # ---------------------------------------------------------

    password_inline_pattern = (
        r"(?i)\b(?:password|passwd|pwd)"
        r"\s*[:=]\s*"
        r"([^\s]+)"
    )

    for match in re.finditer(
        password_inline_pattern,
        text
    ):
        findings.append({
            "type": "PASSWORD",
            "severity": "CRITICAL",
            "confidence": 1.0,
            "start": match.start(1),
            "end": match.end(1)
        })

    password_line_pattern = (
        r"(?im)^[ \t]*"
        r"(?:password|passwd|pwd)"
        r"[ \t]*\r?\n"
        r"[ \t]*([^\s\r\n]+)"
    )

    for match in re.finditer(
        password_line_pattern,
        text
    ):
        findings.append({
            "type": "PASSWORD",
            "severity": "CRITICAL",
            "confidence": 1.0,
            "start": match.start(1),
            "end": match.end(1)
        })

    # ---------------------------------------------------------
    # URL
    # ---------------------------------------------------------

    email_spans = [
        (finding["start"], finding["end"])
        for finding in findings
        if finding["type"] == "EMAIL"
    ]

    url_pattern = (
        r"(?i)\b("
        r"https?://[^\s<>\"\'\)]+"
        r"|"
        r"www\.[a-z0-9.\-]+\.[a-z]{2,}(?::\d+)?(?:/[^\s<>\"\'\)]*)?"
        r"|"
        r"(?<![@\w.-])[a-z0-9\-]+(?:\.[a-z0-9\-]+)*\."
        r"(?:com|org|net|io|dev|ai|app|co|edu|gov|xyz|info|biz|me|cc|tv|online|ly|site|top|live|club|icu|pro|security)"
        r"(?::\d+)?(?:/[^\s<>\"\'\)]*)?(?![@\w])"
        r")"
    )

    for match in re.finditer(url_pattern, text):
        val = match.group(0).rstrip(".,;:!?")
        start = match.start()
        end = start + len(val)

        if any(start < ee and end > es for es, ee in email_spans):
            continue

        if start > 0 and text[start - 1] == "@":
            continue

        findings.append({
            "type": "URL",
            "severity": "MEDIUM",
            "confidence": 1.0,
            "start": start,
            "end": end,
        })

    return findings


if __name__ == "__main__":

    test_text = """
    Username: admin

    Password: DemoPass123

    Password
    AnotherPass456

    Email: demo@example.com
    Email: security@example.com

    Server: 192.168.1.10
    Server: 10.0.0.25
    """

    results = detect_sensitive_data(
        test_text
    )

    print("Basic Detection Results:")

    for result in results:
        print(result)