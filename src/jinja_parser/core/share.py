import base64
import hashlib
import hmac
import json
import zlib
from dataclasses import asdict

from .models import RenderRequest


class ShareCodec:
    def __init__(self, secret: str):
        self._secret = secret.encode("utf-8")

    def encode(self, request: RenderRequest) -> str:
        payload = json.dumps(asdict(request), separators=(",", ":")).encode("utf-8")
        compressed = zlib.compress(payload, level=9)
        sig = hmac.new(self._secret, compressed, hashlib.sha256).digest()[:16]
        token = base64.urlsafe_b64encode(sig + compressed).decode("ascii")
        return token.rstrip("=")

    def decode(self, token: str) -> RenderRequest:
        padded = token + ("=" * ((4 - len(token) % 4) % 4))
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
        if len(raw) < 17:
            raise ValueError("Invalid token.")
        sig = raw[:16]
        compressed = raw[16:]
        expected = hmac.new(self._secret, compressed, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(sig, expected):
            raise ValueError("Invalid token signature.")
        payload = zlib.decompress(compressed)
        parsed = json.loads(payload.decode("utf-8"))
        return RenderRequest(
            template=parsed.get("template", ""),
            data=parsed.get("data", ""),
            render_mode=parsed.get("render_mode", "base"),
            options=parsed.get("options", {}),
            filters=parsed.get("filters", []),
        )

