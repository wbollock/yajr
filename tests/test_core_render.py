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


def test_hash_filter_when_enabled():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ 'hello' | hash('sha256') }}",
        data="{}",
        render_mode="base",
        filters=["hash"],
    )
    assert (
        engine.render(req)
        == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_ipaddr_filter_when_enabled():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ '192.0.2.1/24' | ipaddr('address') }}",
        data="{}",
        render_mode="base",
        filters=["ipaddr"],
    )
    assert engine.render(req) == "192.0.2.1"


def test_filter_not_enabled_fails():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ 'hello' | hash('sha256') }}",
        data="{}",
        render_mode="base",
        filters=[],
    )
    out = engine.render(req)
    assert "Rendering error" in out
