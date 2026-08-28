from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "data" / "signbridge_memory.db"
_LOCK = threading.RLock()

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

def _loads(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default

class SignBridgeMemory:
    """Stores real SignBridge facts only. Natural-language understanding is left to Gemini."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        con.row_factory = sqlite3.Row
        return con

    def _initialize(self) -> None:
        with _LOCK, self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS app_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_app_events_type_id ON app_events(event_type, id DESC)")
            con.commit()

    def set_state(self, key: str, value: Any) -> None:
        key = str(key).strip()
        if not key:
            return
        with _LOCK, self._connect() as con:
            con.execute("""
                INSERT INTO app_state(key, value_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json=excluded.value_json,
                    updated_at=excluded.updated_at
            """, (key, _json(value), _now_iso()))
            con.commit()

    def get_state(self, key: str, default: Any = None) -> Any:
        with _LOCK, self._connect() as con:
            row = con.execute("SELECT value_json FROM app_state WHERE key = ?", (key,)).fetchone()
        return default if row is None else _loads(row["value_json"], default)

    def get_state_with_time(self, key: str) -> dict[str, Any] | None:
        with _LOCK, self._connect() as con:
            row = con.execute("SELECT value_json, updated_at FROM app_state WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return {"value": _loads(row["value_json"]), "updated_at": row["updated_at"]}

    def add_event(self, event_type: str, payload: Any) -> None:
        event_type = str(event_type).strip().lower()
        if not event_type:
            return
        with _LOCK, self._connect() as con:
            con.execute("INSERT INTO app_events(event_type, payload_json, created_at) VALUES (?, ?, ?)",
                        (event_type, _json(payload), _now_iso()))
            con.execute("""
                DELETE FROM app_events
                WHERE event_type = ? AND id NOT IN (
                    SELECT id FROM app_events WHERE event_type = ? ORDER BY id DESC LIMIT 300
                )
            """, (event_type, event_type))
            con.commit()

    def recent_events(self, limit: int = 12) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 50))
        with _LOCK, self._connect() as con:
            rows = con.execute("""
                SELECT event_type, payload_json, created_at
                FROM app_events ORDER BY id DESC LIMIT ?
            """, (limit,)).fetchall()
        return [
            {"type": r["event_type"], "payload": _loads(r["payload_json"], {}), "created_at": r["created_at"]}
            for r in rows
        ]

    def ingest_app_context(self, context: Any) -> None:
        if not isinstance(context, dict):
            return
        speech = context.get("recent_speech")
        if isinstance(speech, str) and speech.strip():
            payload = {"text": speech.strip()}
            old = self.get_state("recent_speech")
            old_text = old.get("text") if isinstance(old, dict) else old
            if old_text != speech.strip():
                self.set_state("recent_speech", payload)
                self.add_event("speech", payload)
        sound = context.get("recent_sound")
        if sound not in (None, "", {}):
            if self.get_state("last_sound") != sound:
                self.set_state("last_sound", sound)
                self.add_event("sound", sound)
        signs = context.get("recent_signs")
        if signs not in (None, "", {}):
            if self.get_state("recent_signs") != signs:
                self.set_state("recent_signs", signs)
                self.add_event("sign", signs)
        education = context.get("education")
        if education not in (None, "", {}):
            self.set_state("education", education)

    def record_context_event(self, event_type: str, payload: Any) -> None:
        event_type = str(event_type).strip().lower()
        if not event_type:
            return
        if event_type == "sound":
            state_key = "last_sound"
        elif event_type in {"speech", "live_speech"}:
            state_key, event_type = "recent_speech", "speech"
        elif event_type in {"sign", "translation"}:
            state_key, event_type = "recent_signs", "sign"
        elif event_type in {"education", "learning"}:
            state_key, event_type = "education", "education"
        else:
            state_key = f"latest_{event_type}"
        self.set_state(state_key, payload)
        self.add_event(event_type, payload)

    def build_context(self) -> dict[str, Any]:
        return {
            "recent_speech": self.get_state_with_time("recent_speech"),
            "last_sound": self.get_state_with_time("last_sound"),
            "recent_signs": self.get_state_with_time("recent_signs"),
            "education": self.get_state_with_time("education"),
            "recent_events": self.recent_events(12),
        }