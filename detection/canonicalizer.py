import unicodedata


ZERO_WIDTH_CHARACTERS = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\u2060",  # WORD JOINER
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE / BOM
}


# Conservative confusable-character mapping.
#
# Only explicitly selected characters are mapped.
# This is intentionally NOT a general Unicode transliterator.
CONFUSABLE_CHARACTER_MAP = {
    # Cyrillic -> Latin
    "\u0430": "a",  # а
    "\u0435": "e",  # е
    "\u043e": "o",  # о
    "\u0440": "p",  # р
    "\u0441": "c",  # с
}


def canonicalize_text(
    text: str,
    enable_confusables: bool = True,
) -> str:
    """
    Apply conservative Unicode canonicalization.

    V3 behavior:
        NFKC + zero-width removal
        enable_confusables=False

    V4 behavior:
        NFKC + zero-width removal
        + selected confusable-character mapping
        enable_confusables=True

    The original user input is never modified at the
    gateway boundary.
    """

    if not text:
        return text

    # 1. Unicode compatibility normalization
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Remove selected zero-width formatting characters
    normalized = "".join(
        character
        for character in normalized
        if character not in ZERO_WIDTH_CHARACTERS
    )

    # 3. Optional V4 homoglyph hardening
    if enable_confusables:
        normalized = "".join(
            CONFUSABLE_CHARACTER_MAP.get(character, character)
            for character in normalized
        )

    return normalized