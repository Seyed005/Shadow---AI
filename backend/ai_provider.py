
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")


async def send_to_approved_ai(text: str):
    """
    Send approved content to the configured local Ollama model.

    Provides the current India date as trusted system context
    without changing the Shadow AI gateway interface.
    """

    if not text or not text.strip():
        return {
            "provider": "OLLAMA",
            "model": OLLAMA_MODEL,
            "status": "ERROR",
            "response": "The AI request was empty."
        }

    try:
        current_date = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%d %B %Y")

        response = await ollama.AsyncClient().chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the approved local AI assistant "
                        "behind the Shadow AI Security Gateway. "
                        f"The current date in India is {current_date}. "
                        "Use this date when answering questions about "
                        "today's date. Never invent live weather, news, "
                        "or other current facts that have not been "
                        "provided by an approved live data source. "
                        "Follow the user's request while respecting "
                        "applicable safety and security requirements."
                    )
                },
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
