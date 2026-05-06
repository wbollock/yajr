import pytest

from jinja_parser.core.models import RenderRequest
from jinja_parser.core.renderer import RenderEngine

ansible = pytest.importorskip  # used below per-test
salt = pytest.importorskip


# ---------------------------------------------------------------------------
# Base mode (SandboxedEnvironment)
# ---------------------------------------------------------------------------

def test_base_blocks_python_object_traversal_rce_pattern():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ ''.__class__.__mro__[1].__subclasses__() }}",
        data="{}",
        render_mode="base",
    )
    out = engine.render(req)
    assert "Rendering error" in out


def test_base_blocks_unsafe_callables():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ cycler.__init__.__globals__ }}",
        data="{}",
        render_mode="base",
    )
    out = engine.render(req)
    assert "Rendering error" in out


def test_base_attr_filter_cannot_leak_dunder_attributes():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ '' | attr('__class__') }}",
        data="{}",
        render_mode="base",
    )
    out = engine.render(req)
    assert "<class" not in out


# ---------------------------------------------------------------------------
# Ansible mode (SandboxedAnsibleEnvironment via worker patch)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ansible_available():
    pytest.importorskip("ansible")


def test_ansible_blocks_python_object_traversal(ansible_available):
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ ''.__class__.__mro__[1].__subclasses__() }}",
        data="{}",
        render_mode="ansible",
    )
    out = engine.render(req)
    assert "Rendering error" in out


def test_ansible_blocks_globals_access(ansible_available):
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ cycler.__init__.__globals__ }}",
        data="{}",
        render_mode="ansible",
    )
    out = engine.render(req)
    assert "Rendering error" in out


def test_ansible_attr_filter_no_dunder_leak(ansible_available):
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ '' | attr('__class__') }}",
        data="{}",
        render_mode="ansible",
    )
    out = engine.render(req)
    assert "<class" not in out


# ---------------------------------------------------------------------------
# Salt mode (empty file_roots / pillar_roots)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def salt_available():
    pytest.importorskip("salt")


def test_salt_cannot_read_host_filesystem(salt_available):
    """salt:// includes must not resolve to the host filesystem."""
    engine = RenderEngine()
    req = RenderRequest(
        template="{% include 'salt:///etc/passwd' %}",
        data="{}",
        render_mode="salt",
    )
    out = engine.render(req)
    assert "root:" not in out


def test_salt_blocks_python_object_traversal(salt_available):
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ ''.__class__.__mro__[1].__subclasses__() }}",
        data="{}",
        render_mode="salt",
    )
    out = engine.render(req)
    assert "Rendering error" in out
