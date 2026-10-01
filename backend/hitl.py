from typing import Literal

from pydantic import BaseModel

from backend.masking import mask_sensitive_data
from backend.ai_provider import send_to_approved_ai


class HITLDecision(BaseModel):
    session_id: str
    decision: Literal[
        "ALLOW",
        "SANITIZE_AND_SEND",
        "BLOCK"
    ]


class SanitizationRequest(BaseModel):
    text: str
    findings: list[dict]


async def process_hitl_decision(
    decision: HITLDecision,
    text: str | None = None,
    findings: list[dict] | None = None
):

    # =====================================================
    # ALLOW
    # =====================================================

    if decision.decision == "ALLOW":

        if text is None:
            return {
                "decision": "ALLOW",
                "status": "ERROR",
                "message": "Text is required."
            }

        ai_response = await send_to_approved_ai(
            text
        )

        return {
            "decision": "ALLOW",
            "status": "APPROVED",
            "forwarded_text": text,
            "ai_response": ai_response,
            "message": "Request approved and forwarded."
        }


    # =====================================================
    # SANITIZE AND SEND
    # =====================================================

    if decision.decision == "SANITIZE_AND_SEND":

        if text is None or findings is None:

            return {
                "decision": "SANITIZE_AND_SEND",
                "status": "ERROR",
                "message": (
                    "Text and findings are required "
                    "for sanitization."
                )
            }


        # Mask sensitive information
        sanitized_text = mask_sensitive_data(
            text,
            findings
        )


        # IMPORTANT:
        # Only sanitized text is sent to AI.

        ai_response = await send_to_approved_ai(
            sanitized_text
        )


        return {
            "decision": "SANITIZE_AND_SEND",
            "status": "SANITIZED",
            "original_text": text,
            "sanitized_text": sanitized_text,
            "ai_response": ai_response,
            "message": (
                "Sensitive information was masked "
                "before forwarding."
            )
        }


    # =====================================================
    # BLOCK
    # =====================================================

    return {
        "decision": "BLOCK",
        "status": "BLOCKED",
        "message": (
            "Request stopped. "
            "No external AI request was made."
        )
    }