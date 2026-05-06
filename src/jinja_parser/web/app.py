import logging
import time
import tomllib
import os
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from jinja_parser.core.models import RenderRequest
from jinja_parser.core.renderer import RenderEngine
from jinja_parser.core.share_store import ShareStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("yajr")

MAX_TEMPLATE_CHARS = 200_000
MAX_DATA_CHARS = 200_000

_LOCALHOST_IPS = {"127.0.0.1", "::1", "localhost"}


class _RateLimiter:
    """Simple in-memory sliding-window rate limiter.

    Not suitable for multi-process deployments — use Redis-backed
    middleware if running multiple uvicorn workers.
    """

    def __init__(self) -> None:
        self._buckets: defaultdict = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, limit: int, window_secs: int) -> bool:
        now = time.monotonic()
        with self._lock:
            ts = self._buckets[key]
            ts[:] = [t for t in ts if now - t < window_secs]
            if len(ts) >= limit:
                return False
            ts.append(now)
            return True


class RenderPayload(BaseModel):
    template: str = Field(default="", max_length=MAX_TEMPLATE_CHARS)
    data: str = Field(default="", max_length=MAX_DATA_CHARS)
    render_mode: str = Field(default="base")
    options: Dict[str, bool] = Field(default_factory=dict)
    filters: List[str] = Field(default_factory=list)

    def to_request(self) -> RenderRequest:
        return RenderRequest(
            template=self.template,
            data=self.data,
            render_mode=self.render_mode,
            options=self.options,
            filters=self.filters,
        )


def _app_version() -> str:
    try:
        pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
        with open(pyproject, "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return "unknown"


def _runtime_version(pkg_name: str) -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version(pkg_name)
    except Exception:
        return "not installed"


def _client_ip(request: Request) -> str:
    trusted_proxies_raw = os.environ.get("YAJR_TRUSTED_PROXIES", "")
    trusted = {p.strip() for p in trusted_proxies_raw.split(",") if p.strip()}
    client_host = request.client.host if request.client else ""
    if trusted and client_host in trusted:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return client_host or "unknown"


def create_app(share_db: Optional[str] = None) -> FastAPI:
    app = FastAPI(title="YAJR")
    engine = RenderEngine()
    db_path = share_db if share_db is not None else os.environ.get("YAJR_SHARE_DB", ":memory:")
    share_store = ShareStore(db_path=db_path)
    stats: Counter = Counter()
    limiter = _RateLimiter()
    root = Path(__file__).resolve().parents[3]
    static_dir = root / "web" / "static"
    template_dir = root / "web" / "templates"
    templates = Jinja2Templates(directory=str(template_dir))
    asset_version = (
        str(int((static_dir / "css" / "site.css").stat().st_mtime)) if static_dir.exists() else "1"
    )
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> RedirectResponse:
        return RedirectResponse(url="/static/favicon.svg")

    @app.get("/healthz")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/render")
    def render(payload: RenderPayload, request: Request) -> Dict[str, str]:
        ip = _client_ip(request)
        if not limiter.is_allowed(f"render:{ip}", limit=30, window_secs=60):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
        stats["renders"] += 1
        log.info("render ip=%s mode=%s", ip, payload.render_mode)
        try:
            return {"render_result": engine.render(payload.to_request())}
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/share")
    def share(payload: RenderPayload, request: Request) -> Dict[str, str]:
        ip = _client_ip(request)
        if not limiter.is_allowed(f"share:{ip}", limit=10, window_secs=60):
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again shortly.")
        stats["shares"] += 1
        token = share_store.create(payload.to_request())
        base = str(request.base_url).rstrip("/")
        log.info("share_create ip=%s token=%s", ip, token)
        return {"token": token, "share_url": f"{base}/s/{token}"}

    @app.get("/api/share/{token}")
    def get_share(token: str, request: Request) -> Dict[str, object]:
        payload = share_store.get(token)
        if payload is None:
            raise HTTPException(status_code=404, detail="Share link not found.")
        stats["share_views"] += 1
        log.info("share_view ip=%s token=%s", _client_ip(request), token)
        return payload

    @app.get("/api/stats")
    def get_stats(request: Request) -> Dict[str, int]:
        ip = _client_ip(request)
        if ip not in _LOCALHOST_IPS:
            raise HTTPException(status_code=403, detail="Stats are only available from localhost.")
        return dict(stats)

    def _base_context(request: Request, initial_token: str) -> Dict[str, object]:
        return {
            "request": request,
            "initial_token": initial_token,
            "asset_version": asset_version,
            "yajr_version": _app_version(),
            "ansible_version": _runtime_version("ansible-core"),
            "salt_version": _runtime_version("salt"),
        }

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        stats["page_views"] += 1
        log.info("page_view ip=%s", _client_ip(request))
        return templates.TemplateResponse(request, "index.html", _base_context(request, ""))

    @app.get("/s/{token}", response_class=HTMLResponse)
    def shared_page(request: Request, token: str):
        stats["page_views"] += 1
        log.info("shared_page_view ip=%s token=%s", _client_ip(request), token)
        return templates.TemplateResponse(request, "index.html", _base_context(request, token))

    return app


app = create_app()
