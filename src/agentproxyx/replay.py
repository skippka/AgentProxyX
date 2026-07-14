from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class ReplayStore:
    def __init__(self, path: str | Path = ".agentproxyx/replay.sqlite"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    kind TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )

    def add(self, kind: str, agent: str, summary: str, data: dict[str, Any] | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events (ts, kind, agent, summary, data) VALUES (?, ?, ?, ?, ?)",
                (time.time(), kind, agent, summary, json.dumps(data or {}, ensure_ascii=False)),
            )

    def recent(self, limit: int = 200) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, ts, kind, agent, summary, data FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        events = []
        for row in reversed(rows):
            events.append(
                {
                    "id": row[0],
                    "ts": row[1],
                    "kind": row[2],
                    "agent": row[3],
                    "summary": row[4],
                    "data": json.loads(row[5]),
                }
            )
        return events

