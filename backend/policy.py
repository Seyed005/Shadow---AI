from typing import Dict


def get_policy_decision(
    risk_result: Dict
) -> Dict:

    risk_score = risk_result["total_risk"]

    # --------------------------------------------------------
    # LOW RISK
    # --------------------------------------------------------
    # Clean / low-risk requests can proceed automatically.
    # --------------------------------------------------------

    if risk_score <= 10:

        return {
            "risk_level": "LOW",
            "decision": "ALLOW",
            "requires_human_review": False
        }

    # --------------------------------------------------------
    # MEDIUM RISK
    # --------------------------------------------------------
    # Human review is required.
    # --------------------------------------------------------

    elif risk_score <= 25:

        return {
            "risk_level": "MEDIUM",
            "decision": "HITL",
            "requires_human_review": True
        }

    # --------------------------------------------------------
    # HIGH RISK
    # --------------------------------------------------------
    # Human review is required.
    # --------------------------------------------------------

    elif risk_score <= 60:

        return {
            "risk_level": "HIGH",
            "decision": "HITL",
            "requires_human_review": True
        }

    # --------------------------------------------------------
    # CRITICAL RISK
    # --------------------------------------------------------
    # CRITICAL DOES NOT automatically block.
    # Human review is required.
    #
    # The actual BLOCK action happens only when the
    # human selects BLOCK through the HITL endpoint.
    # --------------------------------------------------------

    else:

        return {
            "risk_level": "CRITICAL",
            "decision": "HITL",
            "requires_human_review": True
        }