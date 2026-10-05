import os
import re
import secrets
from datetime import datetime, timezone

import bcrypt
import redis.asyncio as redis
from dotenv import load_dotenv


load_dotenv()


# ============================================================
# REDIS CONFIGURATION
# ============================================================

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

REDIS_SESSION_TTL = int(
    os.getenv("REDIS_SESSION_TTL", "3600")
)


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


# ============================================================
# KEY PREFIXES
# ============================================================

USER_KEY_PREFIX = "shadow_ai:user:"
EMAIL_KEY_PREFIX = "shadow_ai:email:"
AUTH_SESSION_KEY_PREFIX = "shadow_ai:auth:"


# ============================================================
# VALIDATION
# ============================================================

USERNAME_PATTERN = re.compile(
    r"^[A-Za-z0-9_.-]{3,32}$"
)

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def validate_username(username: str) -> bool:
    return bool(
        USERNAME_PATTERN.fullmatch(
            username.strip()
        )
    )


def validate_email(email: str) -> bool:
    return bool(
        EMAIL_PATTERN.fullmatch(
            email.strip().lower()
        )
    )


def validate_password(password: str) -> bool:
    return (
        isinstance(password, str)
        and len(password) >= 8
        and len(password) <= 128
    )


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:

    password_bytes = password.encode(
        "utf-8"
    )

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    password: str,
    password_hash: str
) -> bool:

    try:

        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

    except (
        ValueError,
        TypeError,
        UnicodeEncodeError
    ):

        return False


# ============================================================
# ACCOUNT LOOKUP
# ============================================================

async def get_user(
    username: str
):

    username = username.strip()

    raw_user = await redis_client.hgetall(
        f"{USER_KEY_PREFIX}{username}"
    )

    if not raw_user:
        return None

    return raw_user


async def get_user_by_email(
    email: str
):

    email = email.strip().lower()

    username = await redis_client.get(
        f"{EMAIL_KEY_PREFIX}{email}"
    )

    if not username:
        return None

    return await get_user(username)


# ============================================================
# ACCOUNT CREATION
# ============================================================

async def create_user(
    full_name: str,
    username: str,
    email: str,
    password: str
):

    full_name = full_name.strip()
    username = username.strip()
    email = email.strip().lower()

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not full_name:

        raise ValueError(
            "Full name is required."
        )

    if len(full_name) > 100:

        raise ValueError(
            "Full name is too long."
        )

    if not validate_username(username):

        raise ValueError(
            "Username must contain 3-32 characters "
            "using letters, numbers, _, ., or -."
        )

    if not validate_email(email):

        raise ValueError(
            "Invalid email address."
        )

    if not validate_password(password):

        raise ValueError(
            "Password must contain 8-128 characters."
        )

    # --------------------------------------------------------
    # Check duplicate username
    # --------------------------------------------------------

    existing_user = await get_user(
        username
    )

    if existing_user:

        raise ValueError(
            "Username already exists."
        )

    # --------------------------------------------------------
    # Check duplicate email
    # --------------------------------------------------------

    existing_email = await redis_client.get(
        f"{EMAIL_KEY_PREFIX}{email}"
    )

    if existing_email:

        raise ValueError(
            "Email address is already registered."
        )

    # --------------------------------------------------------
    # Hash password
    # --------------------------------------------------------

    password_hash = hash_password(
        password
    )

    # --------------------------------------------------------
    # Create account
    # --------------------------------------------------------

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    user_data = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "password_hash": password_hash,
        "role": "Analyst",
        "created_at": created_at
    }

    # --------------------------------------------------------
    # Store account
    # --------------------------------------------------------

    await redis_client.hset(
        f"{USER_KEY_PREFIX}{username}",
        mapping=user_data
    )

    await redis_client.set(
        f"{EMAIL_KEY_PREFIX}{email}",
        username
    )

    return {
        "username": username,
        "email": email,
        "full_name": full_name,
        "role": "Analyst",
        "created_at": created_at
    }


# ============================================================
# AUTHENTICATION
# ============================================================

async def authenticate_user(
    login: str,
    password: str
):

    login = login.strip()

    if "@" in login:

        user = await get_user_by_email(
            login
        )

    else:

        user = await get_user(
            login
        )

    if not user:

        return None

    if not verify_password(
        password,
        user.get("password_hash", "")
    ):

        return None

    return user


# ============================================================
# AUTH SESSION
# ============================================================

async def create_auth_session(
    username: str
):

    session_token = secrets.token_urlsafe(
        48
    )

    session_data = {
        "username": username,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    session_key = (
        f"{AUTH_SESSION_KEY_PREFIX}"
        f"{session_token}"
    )

    await redis_client.hset(
        session_key,
        mapping=session_data
    )

    await redis_client.expire(
        session_key,
        REDIS_SESSION_TTL
    )

    return session_token


async def get_auth_session(
    session_token: str
):

    if not session_token:
        return None

    session_key = (
        f"{AUTH_SESSION_KEY_PREFIX}"
        f"{session_token}"
    )

    session = await redis_client.hgetall(
        session_key
    )

    if not session:
        return None

    return session


async def delete_auth_session(
    session_token: str
):

    if not session_token:
        return

    session_key = (
        f"{AUTH_SESSION_KEY_PREFIX}"
        f"{session_token}"
    )

    await redis_client.delete(
        session_key
    )


# ============================================================
# PASSWORD RESET TOKEN
# ============================================================

RESET_TOKEN_PREFIX = (
    "shadow_ai:password_reset:"
)

RESET_TOKEN_TTL = 900


async def create_password_reset_token(
    username: str
):

    token = secrets.token_urlsafe(
        32
    )

    key = (
        f"{RESET_TOKEN_PREFIX}"
        f"{token}"
    )

    await redis_client.set(
        key,
        username,
        ex=RESET_TOKEN_TTL
    )

    return token


async def get_password_reset_user(
    token: str
):

    if not token:
        return None

    return await redis_client.get(
        f"{RESET_TOKEN_PREFIX}{token}"
    )


async def delete_password_reset_token(
    token: str
):

    if not token:
        return

    await redis_client.delete(
        f"{RESET_TOKEN_PREFIX}{token}"
    )


# ============================================================
# PASSWORD UPDATE
# ============================================================

async def update_password(
    username: str,
    new_password: str
):

    if not validate_password(
        new_password
    ):

        raise ValueError(
            "Password must contain 8-128 characters."
        )

    user = await get_user(
        username
    )

    if not user:

        raise ValueError(
            "Account not found."
        )

    password_hash = hash_password(
        new_password
    )

    await redis_client.hset(
        f"{USER_KEY_PREFIX}{username}",
        "password_hash",
        password_hash
    )

    return True