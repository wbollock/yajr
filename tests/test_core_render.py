import pytest

from jinja_parser.core.models import RenderRequest
from jinja_parser.core.renderer import RenderEngine


def test_base_mode_renders_yaml_data():
    engine = RenderEngine()
    req = RenderRequest(
        template="hello {{ name }}",
        data="name: world",
        render_mode="base",
    )
    assert engine.render(req) == "hello world"


def test_base_mode_supports_json_data():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ user.name }}",
        data='{"user": {"name": "alice"}}',
        render_mode="base",
    )
    assert engine.render(req) == "alice"


def test_strict_mode_errors_on_undefined():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ missing }}",
        data="{}",
        render_mode="base",
        options={"strict": True},
    )
    out = engine.render(req)
    assert "Rendering error" in out
    assert "missing" in out


def test_trim_and_lstrip_supported():
    engine = RenderEngine()
    req = RenderRequest(
        template="{% if true %}\n  hi\n{% endif %}",
        data="{}",
        render_mode="base",
        options={"trim": True, "lstrip": True},
    )
    assert engine.render(req).startswith("  hi")


def test_unknown_mode_raises():
    engine = RenderEngine()
    req = RenderRequest(template="x", data="{}", render_mode="nope")
    with pytest.raises(ValueError):
        engine.render(req)
