import os

import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")


async def send_to_approved_ai(text: str):
    """
    Send approved content to the configured local Ollama model.

    This function is intentionally kept behind the same interface
    used by the Shadow AI gateway so the gateway logic does not
    depend directly on the AI provider.
    """

    if not text or not text.strip():
        return {
            "provider": "OLLAMA",
            "model": OLLAMA_MODEL,
            "status": "ERROR",
            "response": "The AI request was empty."
        }

    try:
        response = await ollama.AsyncClient().chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        return {
            "provider": "OLLAMA",
            "model": OLLAMA_MODEL,
            "status": "SUCCESS",
            "response": response["message"]["content"]
        }

    except Exception as exc:
        print(
            f"Approved AI provider error: "
            f"{type(exc).__name__}"
        )

        return {
            "provider": "OLLAMA",
            "model": OLLAMA_MODEL,
            "status": "ERROR",
            "response": (
                "The local AI service is temporarily unavailable. "
                "Your request was not forwarded."
            )
        }