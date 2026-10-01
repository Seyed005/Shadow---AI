import json
import redis.asyncio as redis


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

SESSION_TTL = 3600
MAX_HISTORY_TURNS = 20


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


def get_session_key(session_id: str) -> str:
    return f"shadow_ai:session:{session_id}"


async def get_history(session_id: str):
    key = get_session_key(session_id)

    raw_history = await redis_client.get(key)

    if not raw_history:
        return []

    return json.loads(raw_history)


async def save_history(session_id: str, history):
    key = get_session_key(session_id)

    history = history[-MAX_HISTORY_TURNS:]

    await redis_client.set(
        key,
        json.dumps(history),
        ex=SESSION_TTL
    )


def get_pending_hitl_key(session_id: str) -> str:
    return f"shadow_ai:hitl:{session_id}"


async def save_pending_hitl(
    session_id: str,
    request_data: dict
):
    key = get_pending_hitl_key(session_id)

    await redis_client.set(
        key,
        json.dumps(request_data),
        ex=SESSION_TTL
    )


async def get_pending_hitl(session_id: str):
    key = get_pending_hitl_key(session_id)

    raw_request = await redis_client.get(key)

    if not raw_request:
        return {}

    return json.loads(raw_request)


async def delete_pending_hitl(session_id: str):
    key = get_pending_hitl_key(session_id)

    await redis_client.delete(key)


async def close_redis():
    await redis_client.aclose()