from typing import Any, Dict

from jinja2 import StrictUndefined, Undefined
from jinja2.exceptions import TemplateError
from jinja2.sandbox import SandboxedEnvironment

from .models import RenderRequest
from .parse import parse_data_blob


class RenderEngine:
    def render(self, request: RenderRequest) -> str:
        mode = request.normalized_mode()
        if mode not in {"base", "ansible", "salt"}:
            raise ValueError(f"Unknown render mode: {request.render_mode}")

        try:
            data = parse_data_blob(request.data)
            if mode == "base":
                return self._render_base(request.template, data, request.options)
            return self._unsupported_mode(mode)
        except ValueError:
            raise
        except Exception as exc:
            return f"Rendering error:\n\n{exc}"

    def _render_base(
        self, template: str, data: Dict[str, Any], options: Dict[str, bool]
    ) -> str:
        strict = bool(options.get("strict", False))
        trim = bool(options.get("trim", False))
        lstrip = bool(options.get("lstrip", False))

        env = SandboxedEnvironment(
            trim_blocks=trim,
            lstrip_blocks=lstrip,
            undefined=StrictUndefined if strict else Undefined,
            autoescape=False,
        )
        compiled = env.from_string(template)
        return compiled.render(**data)

    def _unsupported_mode(self, mode: str) -> str:
        return (
            "Rendering error:\n\n"
            f"Mode '{mode}' requires optional runtime integration not installed yet."
        )

