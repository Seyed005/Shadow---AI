import unicodedata


ZERO_WIDTH_CHARACTERS = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u2060",  # WORD JOINER
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE / BOM
}


def canonicalize_text(text: str) -> str:
    """
    Apply conservative Unicode canonicalization before
    security-sensitive detection.

    The transformation removes invisible zero-width
    formatting characters that can be used to split
    sensitive keywords while preserving ordinary visible
    text.
    """

    if not text:
        return text

    normalized = unicodedata.normalize(
        "NFKC",
        text
    )

    for character in ZERO_WIDTH_CHARACTERS:
        normalized = normalized.replace(
            character,
            ""
        )

    return normalized