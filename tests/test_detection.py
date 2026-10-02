import pytest

from detection.basic_detector import detect_sensitive_data
from detection.presidio_detector import detect_with_presidio
from detection.custom_recognizers import detect_custom_entities
from detection.normalizer import normalize_findings
from detection.detection_pipeline import run_detection


# =========================================================
# BASIC DETECTOR
# =========================================================

def test_basic_detector_detects_email():

    text = "Contact security@example.com"

    findings = detect_sensitive_data(text)

    types = {
        finding["type"]
        for finding in findings
    }

    assert "EMAIL" in types


def test_basic_detector_detects_ip():

    text = "Internal server: 192.168.10.25"

    findings = detect_sensitive_data(text)

    types = {
        finding["type"]
        for finding in findings
    }

    assert "IP_ADDRESS" in types


# =========================================================
# CUSTOM RECOGNIZERS
# =========================================================

@pytest.mark.parametrize(
    "text",
    [
        "password=DemoPass123",
        "password: DemoPass123",
        "password DemoPass123",
        "employee password DemoPass123",
        "the password is DemoPass123",
        "login password is DemoPass123",
    ]
)
def test_custom_password_detection(text):

    findings = detect_custom_entities(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert password_findings


def test_password_question_is_not_detected():

    text = "What is a password?"

    findings = detect_custom_entities(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert not password_findings


def test_password_reset_question_is_not_detected():

    text = "How do I reset my password?"

    findings = detect_custom_entities(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert not password_findings


def test_employee_id_detection():

    text = "Employee ID: EMP-2026-0051"

    findings = detect_custom_entities(text)

    employee_findings = [
        finding
        for finding in findings
        if finding["type"] == "EMPLOYEE_ID"
    ]

    assert employee_findings


def test_api_key_detection():

    text = "API Key: sk-demo-987654321"

    findings = detect_custom_entities(text)

    api_findings = [
        finding
        for finding in findings
        if finding["type"] == "API_KEY_LIKE"
    ]

    assert api_findings


# =========================================================
# PRESIDIO
# =========================================================

def test_presidio_detects_email():

    text = "Email: security@example.com"

    findings = detect_with_presidio(text)

    types = {
        finding["type"]
        for finding in findings
    }

    assert "EMAIL_ADDRESS" in types


def test_presidio_detects_ip():

    text = "Server: 192.168.10.25"

    findings = detect_with_presidio(text)

    types = {
        finding["type"]
        for finding in findings
    }

    assert "IP_ADDRESS" in types


# =========================================================
# NORMALIZATION
# =========================================================

def test_normalizer_maps_email_address():

    findings = [
        {
            "type": "EMAIL_ADDRESS",
            "source": "PRESIDIO",
            "confidence": 0.95,
            "start": 7,
            "end": 27
        }
    ]

    normalized = normalize_findings(findings)

    assert normalized[0]["type"] == "EMAIL"


def test_normalizer_preserves_password():

    findings = [
        {
            "type": "PASSWORD",
            "source": "CUSTOM",
            "confidence": 0.95,
            "start": 10,
            "end": 21
        }
    ]

    normalized = normalize_findings(findings)

    assert normalized[0]["type"] == "PASSWORD"


def test_normalizer_merges_duplicate_email_findings():

    findings = [
        {
            "type": "EMAIL",
            "source": "BASIC",
            "confidence": 1.0,
            "start": 8,
            "end": 28
        },
        {
            "type": "EMAIL_ADDRESS",
            "source": "PRESIDIO",
            "confidence": 0.95,
            "start": 8,
            "end": 28
        }
    ]

    normalized = normalize_findings(findings)

    email_findings = [
        finding
        for finding in normalized
        if finding["type"] == "EMAIL"
    ]

    assert len(email_findings) == 1

    assert "BASIC" in email_findings[0]["source"]
    assert "PRESIDIO" in email_findings[0]["source"]


# =========================================================
# FULL DETECTION PIPELINE
# =========================================================

def test_full_pipeline_detects_multiple_sensitive_entities():

    text = (
        "Employee ID: EMP-2026-0051\n"
        "Email: security@example.com\n"
        "Internal Server: 192.168.10.25\n"
        "Password: DemoPass456\n"
        "API Key: sk-demo-987654321"
    )

    findings = run_detection(text)

    types = {
        finding["type"]
        for finding in findings
    }

    assert "EMPLOYEE_ID" in types
    assert "EMAIL" in types or "EMAIL_ADDRESS" in types
    assert "IP_ADDRESS" in types
    assert "PASSWORD" in types
    assert "API_KEY_LIKE" in types


def test_full_pipeline_does_not_drop_password():

    text = "Employee password DemoPass123"

    findings = run_detection(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert password_findings


# =========================================================
# V2 BASE64 HARDENING
# =========================================================

def test_pipeline_detects_base64_password():

    text = (
        "Encoded credential: "
        "cGFzc3dvcmQgRGVtb1Bhc3MxMjM="
    )

    findings = run_detection(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert password_findings

    assert any(
        finding["source"].startswith("BASE64")
        for finding in password_findings
    )


def test_pipeline_detects_base64_employee_id():

    text = (
        "Encoded employee ID: "
        "RU1QLTIwMjYtMDA0Mg=="
    )

    findings = run_detection(text)

    employee_findings = [
        finding
        for finding in findings
        if finding["type"] == "EMPLOYEE_ID"
    ]

    assert employee_findings

    assert any(
        finding["source"].startswith("BASE64")
        for finding in employee_findings
    )


# =========================================================
# V3 RED TEAM — UNICODE ZERO-WIDTH BYPASS
# =========================================================

def test_pipeline_detects_zero_width_obfuscated_password():

    text = "pass\u200bword DemoPass123"

    findings = run_detection(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert password_findings


# =========================================================
# V4 RED TEAM — UNICODE HOMOGLYPH BYPASS
# =========================================================

def test_pipeline_detects_homoglyph_obfuscated_password():

    text = "passw\u043erd DemoPass123"

    findings = run_detection(
        text,
        enable_canonicalization=True,
        enable_confusables=True
    )

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert password_findings
    # =========================================================
# V6.1 RED TEAM HARDENING
# =========================================================

def test_custom_detector_detects_semantic_credential_context():

    text = (
        "Use the secret credential "
        "DemoPass123 for the login."
    )

    findings = detect_custom_entities(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert password_findings
    # =========================================================
# V6.1 RED TEAM HARDENING — ROT13 CONTEXT
# =========================================================

def test_pipeline_detects_rot13_obfuscated_password_context():

    text = "cnffjbeq DemoPass123"

    findings = run_detection(text)

    password_findings = [
        finding
        for finding in findings
        if finding["type"] == "PASSWORD"
    ]

    assert password_findings