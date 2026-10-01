import pytest

from backend.risk_engine import calculate_risk
from backend.policy import get_policy_decision


def finding(entity_type, confidence=1.0):
    return {
        "type": entity_type,
        "confidence": confidence
    }


# =========================================================
# ISOLATED RISK
# =========================================================

def test_empty_findings_have_zero_risk():

    result = calculate_risk(
        [],
        []
    )

    assert result["isolated_risk"] == 0
    assert result["historical_risk"] == 0
    assert result["synergy_risk"] == 0


def test_password_has_higher_risk_than_email():

    password_result = calculate_risk(
        [finding("PASSWORD")],
        []
    )

    email_result = calculate_risk(
        [finding("EMAIL")],
        []
    )

    assert (
        password_result["isolated_risk"]
        >
        email_result["isolated_risk"]
    )


def test_confidence_affects_isolated_risk():

    high_confidence = calculate_risk(
        [finding("EMAIL", 1.0)],
        []
    )

    low_confidence = calculate_risk(
        [finding("EMAIL", 0.5)],
        []
    )

    assert (
        high_confidence["isolated_risk"]
        >
        low_confidence["isolated_risk"]
    )


# =========================================================
# HISTORICAL RISK
# =========================================================

def test_previous_risk_contributes_to_historical_risk():

    history = [
        {
            "isolated_risk": 20,
            "findings": []
        }
    ]

    result = calculate_risk(
        [finding("EMAIL")],
        history
    )

    assert result["historical_risk"] > 0


def test_empty_history_has_zero_historical_risk():

    result = calculate_risk(
        [finding("EMAIL")],
        []
    )

    assert result["historical_risk"] == 0


# =========================================================
# SYNERGY / COMBINATION RISK
# =========================================================

def test_multiple_sensitive_entities_can_create_synergy():

    result = calculate_risk(
        [
            finding("EMAIL"),
            finding("PASSWORD")
        ],
        []
    )

    assert result["synergy_risk"] > 0


def test_single_entity_has_no_combination_synergy():

    result = calculate_risk(
        [finding("EMAIL")],
        []
    )

    assert result["synergy_risk"] == 0


# =========================================================
# TOTAL RISK
# =========================================================

def test_total_risk_contains_all_components():

    result = calculate_risk(
        [
            finding("EMAIL"),
            finding("PASSWORD")
        ],
        []
    )

    expected = (
        result["isolated_risk"]
        + result["historical_risk"]
        + result["synergy_risk"]
    )

    assert result["total_risk"] == pytest.approx(
        expected
    )


# =========================================================
# POLICY
# =========================================================

def test_low_risk_policy_allows():

    result = get_policy_decision(
        {"total_risk": 5}
    )

    assert result["risk_level"] == "LOW"
    assert result["decision"] == "ALLOW"
    assert result["requires_human_review"] is False


def test_medium_risk_policy_requires_hitl():

    result = get_policy_decision(
        {"total_risk": 20}
    )

    assert result["risk_level"] == "MEDIUM"
    assert result["decision"] == "HITL"
    assert result["requires_human_review"] is True


def test_high_risk_policy_requires_hitl():

    result = get_policy_decision(
        {"total_risk": 50}
    )

    assert result["risk_level"] == "HIGH"
    assert result["decision"] == "HITL"
    assert result["requires_human_review"] is True


def test_critical_risk_policy_blocks():

    result = get_policy_decision(
        {"total_risk": 80}
    )

    assert result["risk_level"] == "CRITICAL"
    assert result["decision"] == "BLOCK"
    assert result["requires_human_review"] is False


# =========================================================
# POLICY BOUNDARIES
# =========================================================

def test_risk_at_low_threshold_is_allowed():

    result = get_policy_decision(
        {"total_risk": 10}
    )

    assert result["decision"] == "ALLOW"


def test_risk_above_low_threshold_enters_hitl():

    result = get_policy_decision(
        {"total_risk": 11}
    )

    assert result["decision"] == "HITL"


def test_risk_at_medium_boundary_is_hitl():

    result = get_policy_decision(
        {"total_risk": 25}
    )

    assert result["decision"] == "HITL"


def test_risk_above_medium_boundary_is_high_hitl():

    result = get_policy_decision(
        {"total_risk": 26}
    )

    assert result["risk_level"] == "HIGH"
    assert result["decision"] == "HITL"


def test_risk_at_high_boundary_is_high_hitl():

    result = get_policy_decision(
        {"total_risk": 60}
    )

    assert result["risk_level"] == "HIGH"
    assert result["decision"] == "HITL"


def test_risk_above_high_boundary_is_blocked():

    result = get_policy_decision(
        {"total_risk": 61}
    )

    assert result["risk_level"] == "CRITICAL"
    assert result["decision"] == "BLOCK"