import pytest
import uuid
from unittest.mock import AsyncMock, patch

from backend.gateway import (
    process_text,
    process_hitl_decision,
)
from backend import redis_store


# ---------------------------------------------------------
# TEST 1 — CRITICAL REQUEST REQUIRES HITL
#
# Critical requests must NOT be automatically blocked.
# They must wait for a human decision.
#
# The provider must not be called before that decision.
# ---------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_critical_request_requires_hitl():

    session_id = (
        f"boundary-critical-hitl-{uuid.uuid4().hex}"
    )

    with patch(
        "backend.gateway.send_to_approved_ai",
        new_callable=AsyncMock
    ) as mock_provider:

        mock_provider.return_value = {
            "provider": "TEST_PROVIDER",
            "status": "SUCCESS",
            "response": "TEST RESPONSE"
        }

        result = await process_text(
            text=(
                "Password: DemoPass123 "
                "API Key: sk-demo-123456789"
            ),
            session_id=session_id
        )

        assert (
            result["policy"]["risk_level"]
            == "CRITICAL"
        )

        assert (
            result["policy"]["decision"]
            == "HITL"
        )

        assert (
            result["policy"]["requires_human_review"]
            is True
        )

        # No external AI request before human decision.
        mock_provider.assert_not_awaited()


# ---------------------------------------------------------
# TEST 2 — SANITIZE
#
# Provider must receive sanitized text only.
# ---------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_sanitize_sends_only_sanitized_payload():

    session_id = (
        f"boundary-sanitize-test-{uuid.uuid4().hex}"
    )

    original_text = (
        "Please contact security@example.com "
        "about the employee record."
    )

    with patch(
        "backend.gateway.send_to_approved_ai",
        new_callable=AsyncMock
    ) as mock_provider:

        mock_provider.return_value = {
            "provider": "TEST_PROVIDER",
            "status": "SUCCESS",
            "response": "TEST RESPONSE"
        }

        result = await process_text(
            text=original_text,
            session_id=session_id
        )

        if result["policy"]["decision"] == "HITL":

            decision_result = (
                await process_hitl_decision(
                    session_id=session_id,
                    decision="SANITIZE_AND_SEND"
                )
            )

            assert (
                decision_result["status"]
                == "processed"
            )

            sent_payload = (
                mock_provider.await_args.args[0]
            )

            assert (
                "security@example.com"
                not in sent_payload
            )

            assert (
                "analyst@example.com"
                in sent_payload
            )

            assert (
                sent_payload
                != original_text
            )

        elif (
            result["policy"]["decision"]
            == "SANITIZE_AND_SEND"
        ):

            sent_payload = (
                mock_provider.await_args.args[0]
            )

            assert (
                sent_payload
                != original_text
            )

            assert (
                "security@example.com"
                not in sent_payload
            )

        else:

            pytest.fail(
                "Input did not reach "
                "SANITIZE/HITL policy."
            )


# ---------------------------------------------------------
# TEST 3 — ALLOW
#
# Provider must receive original payload unchanged.
# ---------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_allow_sends_original_payload_unchanged():

    session_id = "boundary-allow-test"

    original_text = (
        "Explain the difference between TCP and UDP."
    )

    with patch(
        "backend.gateway.send_to_approved_ai",
        new_callable=AsyncMock
    ) as mock_provider:

        mock_provider.return_value = {
            "provider": "TEST_PROVIDER",
            "status": "SUCCESS",
            "response": "TEST RESPONSE"
        }

        result = await process_text(
            text=original_text,
            session_id=session_id
        )

        assert (
            result["policy"]["decision"]
            == "ALLOW"
        )

        mock_provider.assert_awaited_once_with(
            original_text
        )

        sent_payload = (
            mock_provider.await_args.args[0]
        )

        assert (
            sent_payload
            == original_text
        )


# ---------------------------------------------------------
# TEST 4 — REDIS SESSION ISOLATION
#
# Session A must not see Session B's HITL request.
# ---------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_redis_session_isolation():

    session_a = "boundary-session-A"
    session_b = "boundary-session-B"

    request_a = {
        "text": "Session A private request",
        "findings": [
            {
                "type": "PASSWORD",
                "source": "CUSTOM",
                "confidence": 0.95,
                "start": 10,
                "end": 20
            }
        ]
    }

    request_b = {
        "text": "Session B private request",
        "findings": [
            {
                "type": "EMAIL",
                "source": "BASIC",
                "confidence": 1.0,
                "start": 10,
                "end": 30
            }
        ]
    }

    await redis_store.save_pending_hitl(
        session_a,
        request_a
    )

    await redis_store.save_pending_hitl(
        session_b,
        request_b
    )

    stored_a = (
        await redis_store.get_pending_hitl(
            session_a
        )
    )

    stored_b = (
        await redis_store.get_pending_hitl(
            session_b
        )
    )

    assert (
        stored_a["text"]
        == request_a["text"]
    )

    assert (
        stored_b["text"]
        == request_b["text"]
    )

    assert (
        stored_a["text"]
        != stored_b["text"]
    )

    await redis_store.delete_pending_hitl(
        session_a
    )

    await redis_store.delete_pending_hitl(
        session_b
    )


# ---------------------------------------------------------
# TEST 5 — RAW SECRET BOUNDARY
#
# A password finding is deliberately inserted into a
# pending HITL request. This isolates the enforcement
# boundary from the risk-policy threshold.
#
# Security property:
# SANITIZE_AND_SEND must NEVER send the original secret
# to the approved AI provider.
# ---------------------------------------------------------

@pytest.mark.asyncio(loop_scope="session")
async def test_sanitized_provider_payload_contains_no_raw_secret():

    session_id = "boundary-secret-test"

    secret = "DemoPass123"

    original_text = (
        "Please send password "
        + secret
        + " to security@example.com."
    )

    pending_request = {
        "text": original_text,
        "findings": [
            {
                "type": "PASSWORD",
                "source": "CUSTOM",
                "confidence": 0.95,
                "start": original_text.index(
                    secret
                ),
                "end": (
                    original_text.index(secret)
                    + len(secret)
                )
            },
            {
                "type": "EMAIL",
                "source": "BASIC",
                "confidence": 1.0,
                "start": original_text.index(
                    "security@example.com"
                ),
                "end": (
                    original_text.index(
                        "security@example.com"
                    )
                    + len(
                        "security@example.com"
                    )
                )
            }
        ]
    }

    await redis_store.save_pending_hitl(
        session_id,
        pending_request
    )

    with patch(
        "backend.gateway.send_to_approved_ai",
        new_callable=AsyncMock
    ) as mock_provider:

        mock_provider.return_value = {
            "provider": "TEST_PROVIDER",
            "status": "SUCCESS",
            "response": "TEST RESPONSE"
        }

        result = await process_hitl_decision(
            session_id=session_id,
            decision="SANITIZE_AND_SEND"
        )

        assert (
            result["status"]
            == "processed"
        )

        mock_provider.assert_awaited_once()

        sent_payload = (
            mock_provider.await_args.args[0]
        )

        # Critical security assertions.
        assert secret not in sent_payload

        assert (
            "security@example.com"
            not in sent_payload
        )

        # Sanitized replacements must exist.
        assert (
            "[SYNTHETIC_PASSWORD]"
            in sent_payload
        )

        assert (
            "analyst@example.com"
            in sent_payload
        )

        # Provider must receive modified payload.
        assert (
            sent_payload
            != original_text
        )