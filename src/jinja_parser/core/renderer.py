import hashlib
import ipaddress
from typing import Any, Dict, List

from jinja2 import StrictUndefined, Undefined
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
                return self._render_base(
                    request.template, data, request.options, request.filters
                )
            return self._unsupported_mode(mode)
        except ValueError:
            raise
        except Exception as exc:
            return f"Rendering error:\n\n{exc}"

    def _render_base(
        self,
        template: str,
        data: Dict[str, Any],
        options: Dict[str, bool],
        selected_filters: List[str],
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
        self._register_optional_filters(env, selected_filters)
        compiled = env.from_string(template)
        return compiled.render(**data)

    def _register_optional_filters(
        self, env: SandboxedEnvironment, selected_filters: List[str]
    ) -> None:
        available = {
            "hash": self._filter_hash,
            "ipaddr": self._filter_ipaddr,
        }
        for filter_name in selected_filters:
            if filter_name in available:
                env.filters[filter_name] = available[filter_name]

    def _filter_hash(self, value: Any, algo: str = "sha256") -> str:
        algo_name = str(algo).lower()
        if algo_name not in hashlib.algorithms_available:
            raise ValueError(f"Unsupported hash algorithm: {algo_name}")
        h = hashlib.new(algo_name)
        h.update(str(value).encode("utf-8"))
        return h.hexdigest()

    def _filter_ipaddr(self, value: Any, query: str = "") -> str:
        raw = str(value).strip()
        if "/" in raw:
            iface = ipaddress.ip_interface(raw)
            if query == "address":
                return str(iface.ip)
            if query == "network":
                return str(iface.network)
            return str(iface)

        ip = ipaddress.ip_address(raw)
        if query == "address" or not query:
            return str(ip)
        raise ValueError(f"Unsupported ipaddr query: {query}")

    def _unsupported_mode(self, mode: str) -> str:
        return (
            "Rendering error:\n\n"
            f"Mode '{mode}' requires optional runtime integration not installed yet."
        )
