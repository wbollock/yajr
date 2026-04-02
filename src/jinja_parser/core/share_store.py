import json
import secrets
import sqlite3
import string
import threading
from dataclasses import asdict
from typing import Dict, Optional

from .models import RenderRequest


class ShareStore:
    def __init__(
        self,
        db_path: str = ":memory:",
        max_entries: int = 10000,
        slug_length: int = 8,
    ):
        self._max_entries = max_entries
        self._slug_length = slug_length
        self._alphabet = string.ascii_letters + string.digits
        self._lock = threading.Lock()
        # check_same_thread=False is safe here because all access is
        # serialised through self._lock.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        if db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shares (
                slug        TEXT    PRIMARY KEY,
                payload     TEXT    NOT NULL,
                created_at  INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
            )
            """
        )
        self._conn.commit()

    def create(self, req: RenderRequest) -> str:
        payload = json.dumps(asdict(req))
        with self._lock:
            count = self._conn.execute("SELECT COUNT(*) FROM shares").fetchone()[0]
            if count >= self._max_entries:
                self._conn.execute(
                    "DELETE FROM shares WHERE slug = "
                    "(SELECT slug FROM shares ORDER BY created_at ASC LIMIT 1)"
                )
            for _ in range(8):
                slug = "".join(
                    secrets.choice(self._alphabet) for _ in range(self._slug_length)
                )
                if self._conn.execute(
                    "SELECT 1 FROM shares WHERE slug = ?", (slug,)
                ).fetchone() is None:
                    self._conn.execute(
                        "INSERT INTO shares (slug, payload) VALUES (?, ?)",
                        (slug, payload),
                    )
                    self._conn.commit()
                    return slug

        raise RuntimeError("Could not allocate share slug.")

    def get(self, slug: str) -> Optional[Dict[str, object]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT payload FROM shares WHERE slug = ?", (slug,)
            ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])
