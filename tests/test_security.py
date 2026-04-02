from jinja_parser.core.models import RenderRequest
from jinja_parser.core.renderer import RenderEngine


def test_blocks_python_object_traversal_rce_pattern():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ ''.__class__.__mro__[1].__subclasses__() }}",
        data="{}",
        render_mode="base",
    )
    out = engine.render(req)
    assert "Rendering error" in out


def test_blocks_unsafe_callables():
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ cycler.__init__.__globals__ }}",
        data="{}",
        render_mode="base",
    )
    out = engine.render(req)
    assert "Rendering error" in out


def test_attr_filter_cannot_leak_dunder_attributes():
    """The attr filter must not expose restricted dunder attributes.

    The sandbox may silently return Undefined rather than raising, so the
    meaningful assertion is that class internals are not present in the output,
    not that an error string appears.
    """
    engine = RenderEngine()
    req = RenderRequest(
        template="{{ '' | attr('__class__') }}",
        data="{}",
        render_mode="base",
    )
    out = engine.render(req)
    assert "<class" not in out
