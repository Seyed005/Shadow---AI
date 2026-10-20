
import re


# Conservative rules for common, explicit prompt-injection attempts.
# This is a rule-based detector, not a complete semantic classifier.
PROMPT_INJECTION_PATTERNS = [
    re.compile(
        r"\bignore\s+(?:all\s+)?(?:previous|prior|above|earlier)"
        r"\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdisregard\s+(?:all\s+)?(?:previous|prior|above|earlier)"
        r"\s+instructions\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:reveal|print|show|disclose|repeat)\s+"
        r"(?:the\s+)?(?:hidden\s+|full\s+|original\s+)?"
        r"(?:system|developer)\s+prompt\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bignore\s+(?:your\s+)?safety\s+"
        r"(?:rules|guidelines|instructions|restrictions)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:bypass|disable|override)\s+"
        r"(?:the\s+)?(?:safety|security)\s+"
        r"(?:rules|filters|guardrails|restrictions)\b",
        re.IGNORECASE,
    ),
           re.compile(
        r"\bpretend\s+(?:you\s+are|to\s+be)\s+"
        r"(?:an?\s+)?(?:AI|assistant|model)\b"
        r".{0,120}\b(?:no\s+rules|without\s+restrictions|"
        r"answer\s+anything)\b",
        re.IGNORECASE,
    ),
]


def detect_prompt_injection(text: str) -> list[dict]:
    """Detect explicit prompt-injection phrases using conservative rules."""
    if not text:
        return []

    matches = []

    for pattern in PROMPT_INJECTION_PATTERNS:
        for match in pattern.finditer(text):
            matches.append((match.start(), match.end()))

    # Merge overlapping spans so one phrase is not counted repeatedly.
    matches.sort()
    merged_spans = []

    for start, end in matches:
        if merged_spans and start < merged_spans[-1][1]:
            previous_start, previous_end = merged_spans[-1]
            merged_spans[-1] = (
                previous_start,
                max(previous_end, end),
            )
        else:
            merged_spans.append((start, end))

    return [
        {
            "type": "PROMPT_INJECTION",
            "source": "PROMPT_INJECTION",
            "start": start,
            "end": end,
            "score": 0.95,
            "confidence": 0.95,
            "value": text[start:end],
        }
        for start, end in merged_spans
    ]
