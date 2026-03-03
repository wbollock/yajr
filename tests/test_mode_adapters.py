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


def test_ansible_mode_supports_ansible_specific_filters():
    pytest.importorskip("ansible")
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ {'eth0': 'up', 'eth1': 'down'} | dict2items | length }}|{{ 'vlan-123' | regex_search('[0-9]+') }}",
        data="{}",
        render_mode="ansible",
        options={"strict": True},
    )
    assert engine.render(req) == "2|123"


def test_ansible_mode_to_nice_yaml_filter():
    pytest.importorskip("ansible")
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ {'a': 1, 'b': [2,3]} | to_nice_yaml(indent=2) }}",
        data="{}",
        render_mode="ansible",
    )
    out = engine.render(req)
    assert "a: 1" in out
    assert "b:" in out


def test_salt_mode_serializer_extension_load_yaml():
    pytest.importorskip("salt")
    engine = RenderEngine()
    req = RenderRequest(
        template="{% load_yaml as cfg %}\na: 1\n{% endload %}{{ cfg.a }}",
        data="{}",
        render_mode="salt",
    )
    assert engine.render(req) == "1"


def test_salt_mode_supports_salt_specific_filters():
    pytest.importorskip("salt")
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ {'x': 1, 'y': [2, 3]} | json }}|{{ 'abc' | yaml_dquote }}",
        data="{}",
        render_mode="salt",
        options={"strict": True},
    )
    out = engine.render(req)
    assert '{"x": 1, "y": [2, 3]}' in out
    assert '"abc"' in out
