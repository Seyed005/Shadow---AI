from typing import Dict


def get_policy_decision(risk_result: Dict) -> Dict:

    risk_score = risk_result["total_risk"]

    if risk_score <= 10:
        return {
            "risk_level": "LOW",
            "decision": "ALLOW",
            "requires_human_review": False
        }

    elif risk_score <= 25:
        return {
            "risk_level": "MEDIUM",
            "decision": "HITL",
            "requires_human_review": True
        }

    elif risk_score <= 60:
        return {
            "risk_level": "HIGH",
            "decision": "HITL",
            "requires_human_review": True
        }

    else:
        return {
            "risk_level": "CRITICAL",
            "decision": "BLOCK",
            "requires_human_review": False
        }