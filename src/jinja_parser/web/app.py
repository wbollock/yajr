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
from jinja_parser.core.share import ShareCodec


class RenderPayload(BaseModel):
    template: str = ""
    data: str = ""
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


def create_app(secret: Optional[str] = None) -> FastAPI:
    app = FastAPI(title="Jinja Parser")
    engine = RenderEngine()
    codec = ShareCodec(secret=secret or os.environ.get("JINJA_SHARE_SECRET", "dev-secret"))
    root = Path(__file__).resolve().parents[3]
    static_dir = root / "web" / "static"
    template_dir = root / "web" / "templates"
    templates = Jinja2Templates(directory=str(template_dir))
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
        token = codec.encode(payload.to_request())
        base = str(request.base_url).rstrip("/")
        return {"token": token, "share_url": f"{base}/s/{token}"}

    @app.get("/api/share/{token}")
    def get_share(token: str) -> Dict[str, object]:
        try:
            parsed = codec.decode(token)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return asdict(parsed)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "initial_token": "",
            },
        )

    @app.get("/s/{token}", response_class=HTMLResponse)
    def shared_page(request: Request, token: str):
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "initial_token": token,
            },
        )

    return app


app = create_app()
