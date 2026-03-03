import importlib.metadata
import os
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from jinja_parser.core.models import RenderRequest
from jinja_parser.core.renderer import RenderEngine
from jinja_parser.core.share_store import ShareStore

MAX_TEMPLATE_CHARS = 200_000
MAX_DATA_CHARS = 200_000


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


def _runtime_version(pkg_name: str) -> str:
    try:
        return importlib.metadata.version(pkg_name)
    except importlib.metadata.PackageNotFoundError:
        return "not installed"


def create_app(secret: Optional[str] = None) -> FastAPI:
    app = FastAPI(title="YAJR")
    engine = RenderEngine()
    share_store = ShareStore()
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
    def render(payload: RenderPayload) -> Dict[str, str]:
        return {"render_result": engine.render(payload.to_request())}

    @app.post("/api/share")
    def share(payload: RenderPayload, request: Request) -> Dict[str, str]:
        token = share_store.create(payload.to_request())
        base = str(request.base_url).rstrip("/")
        return {"token": token, "share_url": f"{base}/s/{token}"}

    @app.get("/api/share/{token}")
    def get_share(token: str) -> Dict[str, object]:
        payload = share_store.get(token)
        if payload is None:
            raise HTTPException(status_code=404, detail="Share link not found.")
        return payload

    def _base_context(request: Request, initial_token: str) -> Dict[str, object]:
        return {
            "request": request,
            "initial_token": initial_token,
            "asset_version": asset_version,
            "ansible_version": _runtime_version("ansible-core"),
            "salt_version": _runtime_version("salt"),
        }

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse(request, "index.html", _base_context(request, ""))

    @app.get("/s/{token}", response_class=HTMLResponse)
    def shared_page(request: Request, token: str):
        return templates.TemplateResponse(request, "index.html", _base_context(request, token))

    return app


app = create_app()
