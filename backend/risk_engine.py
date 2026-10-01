from typing import List, Dict


# Starting experimental parameters.
# These values will be tuned during evaluation.
LAMBDA_DECAY = 0.8
ALPHA_SYNERGY = 1.5

TAU_LOW = 10.0
TAU_HITL = 25.0


# Starting weights for different entity types.
ENTITY_WEIGHTS = {
    "PERSON": 10.0,
    "EMAIL": 20.0,
    "PHONE": 20.0,
    "IP_ADDRESS": 30.0,
    "EMPLOYEE_ID": 30.0,
    "PASSWORD": 80.0,
    "API_KEY_LIKE": 90.0,
    "CREDIT_CARD": 90.0,
    "DATABASE_CREDENTIAL": 100.0,
}


def calculate_isolated_risk(findings: List[Dict]) -> float:
    """
    Calculate risk from the current turn only.
    """

    total = 0.0

    for finding in findings:
        entity_type = finding.get("type")

        weight = ENTITY_WEIGHTS.get(entity_type, 0.0)

        confidence = finding.get(
            "confidence",
            1.0
        )

        total += weight * confidence

    return total


def calculate_historical_risk(history: List[Dict]) -> float:
    """
    Calculate risk carried over from previous turns.
    Recent turns have more influence than older turns.
    """

    historical = 0.0
    total_turns = len(history)

    for turn_index, turn in enumerate(history):

        distance = total_turns - turn_index

        historical += (
            LAMBDA_DECAY ** distance
        ) * turn.get("isolated_risk", 0.0)

    return historical


def calculate_synergy(
    current_findings: List[Dict],
    history: List[Dict]
) -> float:
    """
    Add extra risk when sensitive entity types
    appear together across the current session.
    """

    entity_types = set()

    for finding in current_findings:
        entity_types.add(finding.get("type"))

    for turn in history:
        for finding in turn.get("findings", []):
            entity_types.add(finding.get("type"))

    # Initial combination rule.
    # We will generalize this later.
    if (
        "EMAIL" in entity_types
        and "PASSWORD" in entity_types
    ):
        return ALPHA_SYNERGY * 10.0

    if (
        "EMPLOYEE_ID" in entity_types
        and "PASSWORD" in entity_types
    ):
        return ALPHA_SYNERGY * 10.0

    if (
        "API_KEY_LIKE" in entity_types
        and "IP_ADDRESS" in entity_types
    ):
        return ALPHA_SYNERGY * 10.0

    return 0.0


def calculate_risk(
    current_findings: List[Dict],
    history: List[Dict]
) -> Dict:

    isolated_risk = calculate_isolated_risk(
        current_findings
    )

    historical_risk = calculate_historical_risk(
        history
    )

    synergy_risk = calculate_synergy(
        current_findings,
        history
    )

    total_risk = (
        isolated_risk
        + historical_risk
        + synergy_risk
    )

    if total_risk <= TAU_LOW:
        action = "FORWARD"

    elif total_risk <= TAU_HITL:
        action = "QUARANTINE_HITL"

    else:
        action = "BLOCK"

    return {
        "isolated_risk": round(isolated_risk, 2),
        "historical_risk": round(historical_risk, 2),
        "synergy_risk": round(synergy_risk, 2),
        "total_risk": round(total_risk, 2),
        "action": action
    }


if __name__ == "__main__":

    test_findings = [
        {
            "type": "EMAIL",
            "confidence": 1.0
        },
        {
            "type": "PASSWORD",
            "confidence": 1.0
        }
    ]

    test_history = []

    result = calculate_risk(
        test_findings,
        test_history
    )

    print("Risk Engine Test:")
    print(result)