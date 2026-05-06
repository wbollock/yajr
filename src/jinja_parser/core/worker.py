"""Sandboxed rendering subprocess entry-point.

Run as ``python -m jinja_parser.core.worker``.  Reads a JSON-encoded
RenderRequest from stdin, applies hard resource limits, blocks outbound
network access, then writes the render result to stdout as JSON
``{"result": "..."}``.

The parent (RenderEngine.render) enforces an additional wall-clock timeout
and interprets any non-zero exit code as an error.
"""
import json
import resource
import socket as _socket_module
import sys

_OUTPUT_LIMIT_BYTES = 1 * 1024 * 1024  # 1 MB


def _apply_resource_limits() -> None:
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    except (ValueError, OSError):
        pass


def _block_network() -> None:
    """Replace socket.socket so any renderer that dials out fails immediately."""
    class _Blocked:
        def __init__(self, *a, **kw):
            raise OSError("Network access is blocked in the render sandbox.")

        def __getattr__(self, name: str) -> None:  # type: ignore[override]
            raise OSError("Network access is blocked in the render sandbox.")

    _socket_module.socket = _Blocked  # type: ignore[misc]
    try:
        _socket_module.create_connection = (  # type: ignore[attr-defined]
            lambda *a, **kw: (_ for _ in ()).throw(OSError("Network blocked"))
        )
        _socket_module.getaddrinfo = (  # type: ignore[attr-defined]
            lambda *a, **kw: (_ for _ in ()).throw(OSError("Network blocked"))
        )
    except Exception:
        pass


def _patch_ansible_sandbox() -> None:
    """Upgrade Ansible's Jinja environment to use SandboxedEnvironment.

    Patched here, before any Templar is instantiated, so the compiled
    template bytecode includes Jinja's sandbox attribute/callable guards.
    No-op if ansible-core is not installed.
    """
    try:
        import ansible.template as _at
        from jinja2.sandbox import SandboxedEnvironment

        orig = _at.AnsibleEnvironment
        if not issubclass(orig, SandboxedEnvironment):
            _at.AnsibleEnvironment = type(  # type: ignore[attr-defined]
                "_SandboxedAnsibleEnvironment",
                (SandboxedEnvironment, orig),
                {},
            )
    except ImportError:
        pass


def _cap_output(text: str) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= _OUTPUT_LIMIT_BYTES:
        return text
    return (
        encoded[:_OUTPUT_LIMIT_BYTES].decode("utf-8", errors="replace")
        + "\n[output truncated at 1 MB]"
    )


def main() -> None:
    _apply_resource_limits()
    _block_network()
    _patch_ansible_sandbox()

    payload = json.loads(sys.stdin.buffer.read())

    from jinja_parser.core.models import RenderRequest
    from jinja_parser.core.renderer import RenderEngine

    req = RenderRequest(
        template=payload.get("template", ""),
        data=payload.get("data", ""),
        render_mode=payload.get("render_mode", "base"),
        options=payload.get("options", {}),
        filters=payload.get("filters", []),
    )
    try:
        result = RenderEngine()._render_direct(req)
        sys.stdout.write(json.dumps({"result": _cap_output(result)}))
    except ValueError as exc:
        # Input validation errors must propagate to the HTTP layer as 422.
        sys.stdout.write(json.dumps({"result": str(exc), "error_type": "ValueError"}))


if __name__ == "__main__":
    main()
