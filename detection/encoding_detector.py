import base64
import binascii
import re


BASE64_PATTERN = re.compile(
    r"(?<![A-Za-z0-9+/=])"
    r"[A-Za-z0-9+/]{8,}={0,2}"
    r"(?![A-Za-z0-9+/=])"
)


def _looks_like_base64(value: str) -> bool:
    if len(value) < 8:
        return False

    if len(value) % 4 != 0:
        return False

    try:
        decoded = base64.b64decode(
            value,
            validate=True
        )
    except (ValueError, binascii.Error):
        return False

    if not decoded:
        return False

    try:
        decoded_text = decoded.decode(
            "utf-8"
        )
    except UnicodeDecodeError:
        return False

    printable_ratio = sum(
        character.isprintable()
        or character.isspace()
        for character in decoded_text
    ) / len(decoded_text)

    return printable_ratio >= 0.85


def decode_base64_candidates(text: str):
    candidates = []

    for match in BASE64_PATTERN.finditer(text):

        encoded = match.group(0)

        if not _looks_like_base64(encoded):
            continue

        try:
            decoded = base64.b64decode(
                encoded,
                validate=True
            ).decode("utf-8")
        except (
            UnicodeDecodeError,
            ValueError,
            binascii.Error
        ):
            continue

        candidates.append({
            "encoded_value": encoded,
            "decoded_value": decoded,
            "start": match.start(),
            "end": match.end(),
        })

    return candidates