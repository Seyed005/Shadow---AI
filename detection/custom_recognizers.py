import re


# ---------------------------------------------------------
# Employee ID
# ---------------------------------------------------------

EMPLOYEE_ID_PATTERN = re.compile(
    r"\bEMP-\d{4}-\d{4}\b",
    re.IGNORECASE
)


# ---------------------------------------------------------
# API Key / Secret-like values
# ---------------------------------------------------------

API_KEY_PATTERNS = [
    re.compile(
        r"\b(?:sk|pk|api|key|token|secret)[-_]?[A-Za-z0-9_-]{8,}\b",
        re.IGNORECASE
    ),

    re.compile(
        r"\b(?:DEMO_API_KEY|SECRET_KEY|DOCUMENT_API_KEY|DOCUMENT_SECRET_KEY)"
        r"[_-]?[A-Za-z0-9_-]+\b",
        re.IGNORECASE
    )
]


# ---------------------------------------------------------
# Password
# ---------------------------------------------------------

PASSWORD_PATTERNS = [

    # password=DemoPass123
    # password: DemoPass123
    re.compile(
        r"\b(?:password|passwd|pass|pwd)\s*[:=]\s*([^\s,;]+)",
        re.IGNORECASE
    ),

    # password is DemoPass123
    # password equals DemoPass123
    # password equal to DemoPass123
    re.compile(
        r"\b(?:password|passwd|pass|pwd)"
        r"\s+(?:is|equals|equal\s+to)\s+([^\s,;]+)",
        re.IGNORECASE
    ),

    # password DemoPass123
    # employee password DemoPass123
    #
    # Negative lookahead prevents the generic pattern
    # from treating "is", "equals", or "equal" as a password.
    re.compile(
        r"\b(?:password|passwd|pass|pwd)"
        r"\s+(?!(?:is|equals|equal)\b)([^\s,;]+)",
        re.IGNORECASE
    )
]


def detect_custom_entities(text: str):
    """
    Detect Shadow AI project-specific sensitive entities.

    Start/end positions always refer to the original
    input text.
    """

    if not text:
        return []

    findings = []

    # -----------------------------------------------------
    # Employee ID
    # -----------------------------------------------------

    for match in EMPLOYEE_ID_PATTERN.finditer(text):

        findings.append({
            "type": "EMPLOYEE_ID",
            "start": match.start(),
            "end": match.end(),
            "score": 0.95,
            "value": match.group(0)
        })

    # -----------------------------------------------------
    # API keys / secret-like values
    # -----------------------------------------------------

    seen_api_positions = set()

    for pattern in API_KEY_PATTERNS:

        for match in pattern.finditer(text):

            start = match.start()
            end = match.end()

            position = (start, end)

            if position in seen_api_positions:
                continue

            seen_api_positions.add(position)

            findings.append({
                "type": "API_KEY_LIKE",
                "start": start,
                "end": end,
                "score": 0.90,
                "value": match.group(0)
            })

    # -----------------------------------------------------
    # Passwords
    # -----------------------------------------------------

    seen_password_positions = set()

    for pattern in PASSWORD_PATTERNS:

        for match in pattern.finditer(text):

            # Capture group 1 contains only the password value.
            password_value = match.group(1)

            # Get the exact position of capture group 1
            # from the ORIGINAL input text.
            start, end = match.span(1)

            position = (start, end)

            if position in seen_password_positions:
                continue

            seen_password_positions.add(position)

            findings.append({
                "type": "PASSWORD",
                "start": start,
                "end": end,
                "score": 0.95,
                "value": password_value
            })

    return findings


# ---------------------------------------------------------
# Direct test
# ---------------------------------------------------------

if __name__ == "__main__":

    test_cases = [
        "password=DemoPass123",
        "password: DemoPass123",
        "password DemoPass123",
        "employee password DemoPass123",
        "the password is DemoPass123",
        "login password is DemoPass123",
        "How do I reset my password?",
        "What is a password?"
    ]

    print("Custom Recognizer Test Results")
    print("=" * 60)

    for test in test_cases:

        print(f"\nTEST: {test}")

        results = detect_custom_entities(test)

        if results:
            for result in results:
                print(result)
        else:
            print("No sensitive entity detected.")