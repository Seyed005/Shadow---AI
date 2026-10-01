import asyncio

from backend.ai_provider import send_to_approved_ai


async def test():

    text = "Explain cybersecurity in simple words."

    result = await send_to_approved_ai(text)

    print("AI Provider Result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(test())