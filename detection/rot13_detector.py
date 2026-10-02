import codecs


def decode_rot13(text: str) -> str:
    """
    Decode text using ROT13.
    """

    if not text:
        return text

    return codecs.decode(
        text,
        "rot_13"
    )


def detect_rot13_password_context(text: str):
    """
    Detect password context hidden using ROT13.

    The ROT13 transformation is used only to identify
    the hidden password keyword.

    The reported finding always points to the
    original user-supplied credential value.
    """

    if not text:
        return []

    decoded_text = decode_rot13(text)

    lower_decoded = decoded_text.lower()

    password_keywords = (
        "password",
        "passwd",
        "pwd",
    )

    keyword_start = None
    keyword = None

    for candidate in password_keywords:

        position = lower_decoded.find(
            candidate
        )

        if position == -1:
            continue

        if (
            keyword_start is None
            or position < keyword_start
        ):
            keyword_start = position
            keyword = candidate

    if keyword_start is None:
        return []

    value_start = (
        keyword_start + len(keyword)
    )

    while (
        value_start < len(decoded_text)
        and decoded_text[value_start].isspace()
    ):
        value_start += 1

    if (
        value_start < len(decoded_text)
        and decoded_text[value_start] in ":="
    ):
        value_start += 1

        while (
            value_start < len(decoded_text)
            and decoded_text[value_start].isspace()
        ):
            value_start += 1

    value_end = value_start

    while (
        value_end < len(decoded_text)
        and not decoded_text[value_end].isspace()
    ):
        value_end += 1

    if value_end <= value_start:
        return []

    # ROT13 preserves string length and character positions,
    # so the decoded span maps directly to the original text.
    password_value = text[
        value_start:value_end
    ]

    return [{
        "type": "PASSWORD",
        "start": value_start,
        "end": value_end,
        "score": 0.90,
        "confidence": 0.90,
        "value": password_value,
        "decoded_value": decoded_text,
        "source": "ROT13_CUSTOM",
    }]