import secrets
import string
import threading
from dataclasses import asdict
from typing import Dict, Optional

from .models import RenderRequest


class ShareStore:
    def __init__(self, max_entries: int = 10000, slug_length: int = 8):
        self._max_entries = max_entries
        self._slug_length = slug_length
        self._alphabet = string.ascii_letters + string.digits
        self._data: Dict[str, Dict[str, object]] = {}
        self._lock = threading.Lock()

    def create(self, req: RenderRequest) -> str:
        payload = asdict(req)
        with self._lock:
            if len(self._data) >= self._max_entries:
                first = next(iter(self._data))
                self._data.pop(first, None)

            for _ in range(8):
                slug = "".join(secrets.choice(self._alphabet) for _ in range(self._slug_length))
                if slug not in self._data:
                    self._data[slug] = payload
                    return slug

        raise RuntimeError("Could not allocate share slug.")

    def get(self, slug: str) -> Optional[Dict[str, object]]:
        with self._lock:
            return self._data.get(slug)
