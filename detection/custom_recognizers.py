import re


EMPLOYEE_ID_PATTERN = re.compile(
    r"\bEMP-\d{4}-\d{4}\b",
    re.IGNORECASE
)


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


PASSWORD_PATTERNS = [
    re.compile(
        r"\b(?:password|passwd|pass|pwd)\s*[:=]\s*([^\s,;]+)",
        re.IGNORECASE
    ),
    re.compile(
        r"\b(?:password|passwd|pass|pwd)"
        r"\s+(?:is|equals|equal\s+to)\s+([^\s,;]+)",
        re.IGNORECASE
    ),
    re.compile(
        r"\b(?:password|passwd|pass|pwd)"
        r"\s+(?!(?:is|equals|equal)\b)([^\s,;]+)",
        re.IGNORECASE
    )
]

NON_PASSWORD_WORDS = {
    "a", "an", "the", "for", "to", "in", "on", "at", "by", "from", "of", "with",
    "and", "or", "but", "not", "so", "as", "if", "that", "this", "which",
    "management", "manager", "managers", "policy", "policies", "security",
    "reset", "resets", "resetting", "change", "changes", "changing", "update", "updates", "updating",
    "creation", "create", "creating", "protect", "protection", "generator", "generators",
    "length", "strength", "complexity", "rule", "rules", "guideline", "guidelines",
    "best", "practice", "practices", "requirement", "requirements", "hash", "hashes", "hashing",
    "cracker", "cracking", "checker", "check", "checks", "checking", "audit", "auditing",
    "field", "fields", "input", "inputs", "box", "boxes", "form", "forms",
    "leak", "leaks", "leaked", "breach", "breaches", "breached", "stolen", "compromised",
    "vault", "vaults", "store", "storage", "storing", "schema", "database", "table", "column",
    "file", "files", "list", "lists", "type", "types", "sample", "samples", "example", "examples",
    "test", "tests", "testing", "verification", "verify", "verifying", "pattern", "patterns",
    "flow", "flows", "system", "systems", "service", "services", "tool", "tools",
    "app", "apps", "application", "applications", "user", "users", "account", "accounts",
    "admin", "admins", "help", "tips", "support", "question", "questions",
    "issue", "issues", "error", "errors", "problem", "problems",
    "information", "data", "details", "text", "string", "value", "values",
    "prompt", "prompts", "model", "models", "ai", "gateway", "assistant"
}


# V6.1:
# Conservative semantic credential patterns.
#
# These patterns require explicit credential context rather
# than classifying arbitrary secret-looking strings as passwords.
#
# Examples:
#   secret credential DemoPass123
#   secret password DemoPass123
#   login credential DemoPass123
#   authentication credential DemoPass123
#
# The credential value must also contain both letters and digits.
SEMANTIC_CREDENTIAL_PATTERNS = [
    re.compile(
        r"\bsecret\s+(?:credential|password)"
        r"\s+([A-Za-z0-9][A-Za-z0-9!@#$%^&*_.-]{5,})\b",
        re.IGNORECASE
    ),
    re.compile(
        r"\b(?:login|authentication)\s+credential"
        r"\s+([A-Za-z0-9][A-Za-z0-9!@#$%^&*_.-]{5,})\b",
        re.IGNORECASE
    ),
]


def detect_custom_entities(text: str):
    if not text:
        return []

    findings = []

    for match in EMPLOYEE_ID_PATTERN.finditer(text):
        findings.append({
            "type": "EMPLOYEE_ID",
            "start": match.start(),
            "end": match.end(),
            "score": 0.95,
            "value": match.group(0)
        })

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

    seen_password_positions = set()

    for pattern in PASSWORD_PATTERNS:
        for match in pattern.finditer(text):
            password_value = match.group(1)
            clean_val = password_value.strip().rstrip("?.!,:;\"'").lower()
            if pattern == PASSWORD_PATTERNS[2] and clean_val in NON_PASSWORD_WORDS:
                continue

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

    # ---------------------------------------------------------
    # V6.1 SEMANTIC CREDENTIAL DETECTION
    # ---------------------------------------------------------

    for pattern in SEMANTIC_CREDENTIAL_PATTERNS:
        for match in pattern.finditer(text):

            credential_value = match.group(1)

            # Require both alphabetic and numeric characters.
            # This avoids classifying generic words as passwords.
            if not (
                re.search(r"[A-Za-z]", credential_value)
                and re.search(r"\d", credential_value)
            ):
                continue

            start, end = match.span(1)
            position = (start, end)

            if position in seen_password_positions:
                continue

            seen_password_positions.add(position)

            findings.append({
                "type": "PASSWORD",
                "start": start,
                "end": end,
                "score": 0.90,
                "value": credential_value
            })

    return findings