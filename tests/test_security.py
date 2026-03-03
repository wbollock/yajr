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
