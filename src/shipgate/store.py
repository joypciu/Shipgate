from __future__ import annotations

import sqlite3
from pathlib import Path


class DeliveryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS deliveries (
                    repo TEXT NOT NULL,
                    sha TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    comment_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (repo, sha)
                )
                """
            )

    def seen(self, repo: str, sha: str) -> bool:
        with self._conn() as connection:
            row = connection.execute(
                "SELECT 1 FROM deliveries WHERE repo = ? AND sha = ?",
                (repo, sha),
            ).fetchone()
        return row is not None

    def record(self, repo: str, sha: str, run_id: str, comment_id: int) -> None:
        with self._conn() as connection:
            connection.execute(
                "INSERT INTO deliveries (repo, sha, run_id, comment_id) VALUES (?, ?, ?, ?)",
                (repo, sha, run_id, comment_id),
            )

    def _conn(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection
