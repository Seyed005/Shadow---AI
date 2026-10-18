from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "shadow_ai_conversations.db"

MAX_CONTENT_LENGTH = 12000
MAX_TITLE_LENGTH = 80


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            username TEXT NOT NULL,
            session_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            PRIMARY KEY (username, session_id)
        );

        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            input_type TEXT,
            file_name TEXT,
            decision TEXT,
            risk_level TEXT,
            risk_score REAL,
            redacted INTEGER NOT NULL DEFAULT 0,
            metadata_json TEXT,
            created_at INTEGER NOT NULL,
            FOREIGN KEY (username, session_id)
                REFERENCES conversations(username, session_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
            ON conversations(username, updated_at DESC);

        CREATE INDEX IF NOT EXISTS idx_messages_user_session
            ON conversation_messages(username, session_id, id);
        """
    )
    conn.commit()


def _safe(value, limit: int = MAX_CONTENT_LENGTH) -> str:
    value = "" if value is None else str(value)
    return value[:limit]


def _title_from(content: str, file_name: Optional[str] = None) -> str:
    if file_name:
        title = str(file_name).strip()
    else:
        title = " ".join(str(content or "").split()).strip()

    if not title:
        title = "New secure chat"

    return title[:MAX_TITLE_LENGTH]


async def ensure_conversation(
    username: str,
    session_id: str,
    title: Optional[str] = None,
) -> None:
    now = int(time.time())

    with _connect() as conn:
        _init_db(conn)
        row = conn.execute(
            """
            SELECT 1
            FROM conversations
            WHERE username = ? AND session_id = ?
            """,
            (username, session_id),
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO conversations
                    (username, session_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    username,
                    session_id,
                    _title_from(title or ""),
                    now,
                    now,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE conversations
                SET updated_at = ?
                WHERE username = ? AND session_id = ?
                """,
                (now, username, session_id),
            )

        conn.commit()


async def record_gateway_result(
    *,
    username: str,
    session_id: str,
    safe_user_content: str,
    result: dict,
    file_name: Optional[str] = None,
) -> None:
    await ensure_conversation(
        username,
        session_id,
        title=file_name or safe_user_content,
    )

    now = int(time.time())
    policy = result.get("policy") or {}
    risk = result.get("risk") or {}
    findings = result.get("findings") or []

    decision = str(policy.get("decision") or "").upper() or None
    risk_level = policy.get("risk_level") or risk.get("risk_level")
    risk_score = risk.get("total_risk")
    if risk_score is None:
        risk_score = risk.get("risk_score")

    metadata = {
        "finding_types": [
            f.get("type")
            for f in findings
            if isinstance(f, dict) and f.get("type")
        ],
        "history_turns": result.get("history_turns"),
        "has_sanitized_text": bool(result.get("sanitized_text")),
    }

    ai_response = result.get("ai_response")
    assistant_text = ""
    if isinstance(ai_response, dict):
        assistant_text = ai_response.get("response") or ""
    elif ai_response is not None:
        assistant_text = str(ai_response)

    safe_user_content = _safe(safe_user_content)
    assistant_text = _safe(assistant_text)

    with _connect() as conn:
        _init_db(conn)

        conn.execute(
            """
            INSERT INTO conversation_messages
                (
                    username, session_id, role, content,
                    input_type, file_name, decision,
                    risk_level, risk_score, redacted,
                    metadata_json, created_at
                )
            VALUES (?, ?, 'user', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                session_id,
                safe_user_content,
                result.get("input_type"),
                file_name or result.get("file_name"),
                decision,
                risk_level,
                risk_score,
                1 if findings else 0,
                json.dumps(metadata, ensure_ascii=False),
                now,
            ),
        )

        if assistant_text:
            conn.execute(
                """
                INSERT INTO conversation_messages
                    (
                        username, session_id, role, content,
                        input_type, decision, created_at
                    )
                VALUES (?, ?, 'assistant', ?, ?, ?, ?)
                """,
                (
                    username,
                    session_id,
                    assistant_text,
                    result.get("input_type"),
                    decision,
                    now,
                ),
            )

        conn.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE username = ? AND session_id = ?
            """,
            (now, username, session_id),
        )
        conn.commit()


async def complete_pending_hitl(
    *,
    username: str,
    session_id: str,
    decision: str,
    safe_sanitized_text: Optional[str] = None,
    ai_response: Optional[dict] = None,
) -> None:
    now = int(time.time())
    decision = decision.upper().strip()

    assistant_text = ""
    if isinstance(ai_response, dict):
        assistant_text = ai_response.get("response") or ""
    elif ai_response is not None:
        assistant_text = str(ai_response)

    with _connect() as conn:
        _init_db(conn)

        row = conn.execute(
            """
            SELECT id
            FROM conversation_messages
            WHERE username = ?
              AND session_id = ?
              AND role = 'user'
            ORDER BY id DESC
            LIMIT 1
            """,
            (username, session_id),
        ).fetchone()

        if row is None:
            raise ValueError("No pending conversation message found.")

        metadata = {
            "has_sanitized_text": bool(safe_sanitized_text),
            "hitl_completed": True,
        }

        conn.execute(
            """
            UPDATE conversation_messages
            SET decision = ?,
                metadata_json = ?,
                created_at = created_at
            WHERE id = ?
            """,
            (
                decision,
                json.dumps(metadata, ensure_ascii=False),
                row["id"],
            ),
        )

        if safe_sanitized_text:
            conn.execute(
                """
                INSERT INTO conversation_messages
                    (
                        username, session_id, role, content,
                        input_type, decision, redacted, created_at
                    )
                VALUES (?, ?, 'security', ?, 'TEXT', ?, 1, ?)
                """,
                (
                    username,
                    session_id,
                    _safe(
                        "WHAT AI WILL RECEIVE:\n"
                        + safe_sanitized_text
                    ),
                    decision,
                    now,
                ),
            )

        if assistant_text:
            conn.execute(
                """
                INSERT INTO conversation_messages
                    (
                        username, session_id, role, content,
                        input_type, decision, created_at
                    )
                VALUES (?, ?, 'assistant', ?, 'TEXT', ?, ?)
                """,
                (
                    username,
                    session_id,
                    _safe(assistant_text),
                    decision,
                    now,
                ),
            )

        conn.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE username = ? AND session_id = ?
            """,
            (now, username, session_id),
        )
        conn.commit()


async def list_conversations(username: str) -> list[dict]:
    with _connect() as conn:
        _init_db(conn)
        rows = conn.execute(
            """
            SELECT
                session_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE username = ?
            ORDER BY updated_at DESC
            """,
            (username,),
        ).fetchall()

    return [dict(row) for row in rows]


async def get_conversation(
    username: str,
    session_id: str,
) -> Optional[dict]:
    with _connect() as conn:
        _init_db(conn)

        conversation = conn.execute(
            """
            SELECT
                session_id,
                title,
                created_at,
                updated_at
            FROM conversations
            WHERE username = ? AND session_id = ?
            """,
            (username, session_id),
        ).fetchone()

        if conversation is None:
            return None

        messages = conn.execute(
            """
            SELECT
                id,
                role,
                content,
                input_type,
                file_name,
                decision,
                risk_level,
                risk_score,
                redacted,
                metadata_json,
                created_at
            FROM conversation_messages
            WHERE username = ? AND session_id = ?
            ORDER BY id ASC
            """,
            (username, session_id),
        ).fetchall()

    result_messages = []
    for row in messages:
        item = dict(row)
        raw_metadata = item.pop("metadata_json", None)
        try:
            item["metadata"] = json.loads(raw_metadata) if raw_metadata else {}
        except json.JSONDecodeError:
            item["metadata"] = {}
        item["redacted"] = bool(item["redacted"])
        result_messages.append(item)

    return {
        **dict(conversation),
        "messages": result_messages,
    }
