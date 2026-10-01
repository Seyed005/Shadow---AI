async def send_to_approved_ai(text: str):
    """
    Mock approved AI provider.

    This simulates sending the final safe prompt
    to an approved external AI API.
    """

    print("\n========== APPROVED AI API ==========")

    print("Prompt forwarded to AI:")

    print(text)

    print("=====================================\n")

    return {
        "provider": "MOCK_APPROVED_AI",

        "status": "SUCCESS",

        "response": (
            "Mock AI response: "
            "The request was safely processed."
        )
    }