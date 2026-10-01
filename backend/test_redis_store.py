import asyncio

from backend.redis_store import save_history, get_history


async def main():

    test_history = [
        {
            "isolated_risk": 80,
            "findings": [
                {
                    "type": "PASSWORD"
                }
            ]
        }
    ]

    await save_history(
        "demo-session",
        test_history
    )

    result = await get_history(
        "demo-session"
    )

    print("Redis Test Result:")
    print(result)


asyncio.run(main())