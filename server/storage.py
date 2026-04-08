import os
import json
import uuid
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
import sqlite3

import re

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "conversations")
DB_PATH = os.getenv("SESSIONS_DB_PATH", os.path.join(os.path.dirname(__file__), "data", "sessions.db"))

# Strict UUID validation regex
UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _get_conn() -> sqlite3.Connection:
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_db() -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                current_stage INTEGER NOT NULL DEFAULT 1,
                data_json TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC)")

def _migrate_json_files_if_needed() -> None:
    """
    One-time best-effort migration from existing JSON files to SQLite.
    Keeps old files untouched so rollback is still possible.
    """
    ensure_data_dir()
    _ensure_db()

    with _get_conn() as conn:
        row = conn.execute("SELECT COUNT(1) AS count FROM conversations").fetchone()
        if row and int(row["count"]) > 0:
            return

        migrated = 0
        for filename in os.listdir(DATA_DIR):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(DATA_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    stored_data = json.load(f)

                conv_id = stored_data.get("id")
                if not conv_id or not UUID_REGEX.match(conv_id):
                    continue

                created_at = stored_data.get("created_at") or datetime.utcnow().isoformat()

                if "data" in stored_data and isinstance(stored_data["data"], dict):
                    frontend_state = stored_data["data"]
                    title = stored_data.get("title") or frontend_state.get("question", "Untitled")[:50]
                    current_stage = int(stored_data.get("current_stage", frontend_state.get("currentStage", 1)))
                else:
                    # Legacy message format fallback.
                    messages = stored_data.get("messages", [])
                    user_msg = next((m for m in messages if m.get("role") == "user"), None)
                    assistant_msg = next((m for m in messages if m.get("role") == "assistant"), None)

                    question = user_msg.get("content", "") if user_msg else ""
                    stage1_responses = []
                    selected_models = []
                    for item in assistant_msg.get("stage1", []) if assistant_msg else []:
                        model = item.get("model", "")
                        response = item.get("response", "")
                        stage1_responses.append({"model": model, "response": response})
                        if model:
                            selected_models.append(model)

                    stage2_reviews = []
                    for item in assistant_msg.get("stage2", []) if assistant_msg else []:
                        stage2_reviews.append({
                            "model": item.get("model", ""),
                            "review": item.get("ranking", "")
                        })

                    stage3_data = assistant_msg.get("stage3") if assistant_msg else None
                    stage3_result = None
                    if stage3_data:
                        stage3_result = {
                            "final_answer": stage3_data.get("response", ""),
                            "aggregate_rankings": [],
                            "chairman_model": stage3_data.get("model")
                        }

                    current_stage = int(stored_data.get("current_stage", 1))
                    if "current_stage" not in stored_data:
                        if stage3_result:
                            current_stage = 3
                        elif stage2_reviews:
                            current_stage = 2
                        elif stage1_responses:
                            current_stage = 2

                    frontend_state = {
                        "id": conv_id,
                        "question": question,
                        "selectedModels": selected_models,
                        "stage1Responses": stage1_responses,
                        "stage2Reviews": stage2_reviews,
                        "stage3Result": stage3_result,
                        "currentStage": current_stage,
                    }
                    title = stored_data.get("title") or question[:50] or "Untitled"

                conn.execute(
                    """
                    INSERT OR IGNORE INTO conversations (id, title, created_at, current_stage, data_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        conv_id,
                        title,
                        created_at,
                        current_stage,
                        json.dumps(frontend_state),
                    ),
                )
                migrated += 1
            except Exception as e:
                logger.warning(f"Skipping migration for {filename}: {e}")

        if migrated:
            logger.info(f"Migrated {migrated} conversation file(s) to SQLite: {DB_PATH}")

_migrate_json_files_if_needed()

def list_conversations() -> List[Dict]:
    _ensure_db()
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, title, created_at
            FROM conversations
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        {
            "id": row["id"],
            "title": row["title"] or "Untitled",
            "created_at": row["created_at"],
            "data": None,
        }
        for row in rows
    ]

def get_conversation(conversation_id: str) -> Optional[Dict]:
    _ensure_db()

    # Security: Validate ID is a UUID.
    if not UUID_REGEX.match(conversation_id):
        logger.warning(f"Invalid conversation ID format attempt blocked: {conversation_id}")
        return None

    try:
        with _get_conn() as conn:
            row = conn.execute(
                """
                SELECT id, title, created_at, current_stage, data_json
                FROM conversations
                WHERE id = ?
                """,
                (conversation_id,),
            ).fetchone()

        if row is None:
            return None

        data = json.loads(row["data_json"])
        data["id"] = row["id"]
        if "currentStage" not in data:
            data["currentStage"] = int(row["current_stage"])

        return {
            "id": row["id"],
            "title": row["title"],
            "created_at": row["created_at"],
            "data": data,
        }
    except Exception as e:
        logger.error(f"Error reading conversation {conversation_id}: {e}")
        return None

def save_conversation(frontend_state: Dict) -> Dict:
    _ensure_db()
    
    conv_id = frontend_state.get("id") or str(uuid.uuid4())
    # Ensure ID is in the state object
    frontend_state['id'] = conv_id

    # Security: Validate ID is a UUID to prevent path traversal.
    if not UUID_REGEX.match(conv_id):
        logger.warning(f"Invalid conversation ID format attempt blocked: {conv_id}")
        return {"error": "Invalid conversation ID"}

    created_at = datetime.utcnow().isoformat()

    title = frontend_state.get("question", "Untitled")[:50]
    current_stage = int(frontend_state.get("currentStage", 1))

    # Preserve created_at for updates.
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT created_at FROM conversations WHERE id = ?",
            (conv_id,),
        ).fetchone()
        if existing:
            created_at = existing["created_at"]

        conn.execute(
            """
            INSERT INTO conversations (id, title, created_at, current_stage, data_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                current_stage = excluded.current_stage,
                data_json = excluded.data_json
            """,
            (
                conv_id,
                title,
                created_at,
                current_stage,
                json.dumps(frontend_state),
            ),
        )

    # Prepare data to be returned and saved
    # The frontend expects this structure.
    response_data = {
        "id": conv_id,
        "title": title,
        "created_at": created_at,
        "data": frontend_state
    }
    response_data["current_stage"] = current_stage
        
    return response_data

def delete_conversation(conversation_id: str) -> bool:
    _ensure_db()

    # Security: Validate ID is a UUID.
    if not UUID_REGEX.match(conversation_id):
        logger.warning(f"Invalid conversation ID format attempt blocked: {conversation_id}")
        return False

    try:
        with _get_conn() as conn:
            cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        return False
