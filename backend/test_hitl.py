import asyncio
from backend.hitl import (
    HITLDecision,
    process_hitl_decision
)


async def main():
    test_decisions = [
        "ALLOW",
        "SANITIZE_AND_SEND",
        "BLOCK"
    ]

    for decision in test_decisions:
        request = HITLDecision(
            session_id="hitl-test-001",
            decision=decision
        )

        result = await process_hitl_decision(
            request
        )

        print(
            f"{decision} → {result}"
        )


if __name__ == "__main__":
    asyncio.run(main())