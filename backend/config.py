import os


APP_NAME = "Shadow AI Security Gateway"
APP_VERSION = "0.1.0"

HOST = os.getenv("SHADOW_AI_HOST", "127.0.0.1")
PORT = int(os.getenv("SHADOW_AI_PORT", "8000"))

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

REDIS_SESSION_TTL = int(
    os.getenv("REDIS_SESSION_TTL", "3600")
)

MAX_HISTORY_TURNS = int(
    os.getenv("MAX_HISTORY_TURNS", "20")
)