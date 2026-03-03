import pytest

from jinja_parser.core.models import RenderRequest
from jinja_parser.core.renderer import RenderEngine


def test_ansible_mode_basic_render():
    pytest.importorskip("ansible")
    engine = RenderEngine()
    req = RenderRequest(
        template="hello {{ name }}",
        data="name: world",
        render_mode="ansible",
    )
    assert engine.render(req) == "hello world"


def test_ansible_mode_strict_check_error():
    pytest.importorskip("ansible")
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ missing }}",
        data="{}",
        render_mode="ansible",
        options={"strict": True},
    )
    out = engine.render(req)
    assert "Rendering error" in out


def test_salt_mode_basic_render():
    pytest.importorskip("salt")
    engine = RenderEngine()
    req = RenderRequest(
        template="hello {{ name }}",
        data="name: world",
        render_mode="salt",
    )
    assert engine.render(req) == "hello world"


def test_salt_mode_strict_check_error():
    pytest.importorskip("salt")
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ missing }}",
        data="{}",
        render_mode="salt",
        options={"strict": True},
    )
    out = engine.render(req)
    assert "Rendering error" in out
