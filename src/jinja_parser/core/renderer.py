import hashlib
import ipaddress
import tempfile
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
            if mode == "ansible":
                return self._render_ansible(
                    request.template, data, request.options, request.filters
                )
            return self._render_salt(
                request.template, data, request.options, request.filters
            )
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
        env.filters.update(self._optional_filter_map(selected_filters))
        compiled = env.from_string(template)
        return compiled.render(**data)

    def _render_ansible(
        self,
        template: str,
        data: Dict[str, Any],
        options: Dict[str, bool],
        selected_filters: List[str],
    ) -> str:
        try:
            from ansible.parsing.dataloader import DataLoader
            from ansible.template import Templar
        except ImportError as exc:
            return f"Rendering error:\n\nAnsible runtime unavailable: {exc}"

        strict = bool(options.get("strict", False))
        trim = bool(options.get("trim", False))
        lstrip = bool(options.get("lstrip", False))

        templar = Templar(loader=DataLoader(), variables=data)
        templar.environment.filters.update(self._optional_filter_map(selected_filters))

        return templar.template(
            template,
            fail_on_undefined=strict,
            overrides={"trim_blocks": trim, "lstrip_blocks": lstrip},
            disable_lookups=True,
        )

    def _render_salt(
        self,
        template: str,
        data: Dict[str, Any],
        options: Dict[str, bool],
        selected_filters: List[str],
    ) -> str:
        try:
            import salt.utils.templates as salt_templates
        except ImportError as exc:
            return f"Rendering error:\n\nSalt runtime unavailable: {exc}"

        strict = bool(options.get("strict", False))
        trim = bool(options.get("trim", False))
        lstrip = bool(options.get("lstrip", False))

        with tempfile.TemporaryDirectory(prefix="jparser-salt-cache-") as cachedir:
            opts = {
                "cachedir": cachedir,
                "file_client": "local",
                "renderer": "jinja|yaml",
                "id": "jparser",
                "allow_undefined": not strict,
                "jinja_env": {
                    "trim_blocks": trim,
                    "lstrip_blocks": lstrip,
                },
            }
            context = {
                "opts": opts,
                "saltenv": "base",
            }
            context.update(data)

            originals: Dict[str, Any] = {}
            custom = self._optional_filter_map(selected_filters)
            for name, func in custom.items():
                originals[name] = salt_templates.JinjaFilter.salt_jinja_filters.get(name)
                salt_templates.JinjaFilter.salt_jinja_filters[name] = func

            try:
                return salt_templates.render_jinja_tmpl(template, context)
            finally:
                for name in custom:
                    if originals[name] is None:
                        salt_templates.JinjaFilter.salt_jinja_filters.pop(name, None)
                    else:
                        salt_templates.JinjaFilter.salt_jinja_filters[name] = originals[name]

    def _optional_filter_map(self, selected_filters: List[str]) -> Dict[str, Any]:
        available = {
            "hash": self._filter_hash,
            "ipaddr": self._filter_ipaddr,
        }
        chosen: Dict[str, Any] = {}
        for filter_name in selected_filters:
            if filter_name in available:
                chosen[filter_name] = available[filter_name]
        return chosen

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
