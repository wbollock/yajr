"""Tests for subprocess worker resource limits and output cap."""
import pytest

from jinja_parser.core.models import RenderRequest
from jinja_parser.core.renderer import RenderEngine


def _engine():
    return RenderEngine()


def test_output_is_capped():
    """Template output longer than 1 MB is truncated with a marker."""
    e = _engine()
    req = RenderRequest(
        template="{{ val }}",
        data="val: " + "x" * 2_000_000,
        render_mode="base",
    )
    result = e.render(req)
    assert "truncated" in result
    assert len(result.encode("utf-8")) <= 1_200_000


def test_cpu_exhaustion_returns_error():
    """A runaway loop is killed within the timeout and returns an error string.

    This test takes up to ~8 s (YAJR_WORKER_TIMEOUT default) while the worker
    runs until RLIMIT_CPU fires.  It is intentionally slow.
    """
    e = _engine()
    req = RenderRequest(
        template="{% for i in range(10000000000) %}x{% endfor %}",
        data="{}",
        render_mode="base",
    )
    result = e.render(req)
    assert "error" in result.lower() or "timed out" in result.lower()


def test_invalid_mode_raises_value_error():
    """An unknown render_mode propagates as ValueError (yields 422 from the API)."""
    e = _engine()
    req = RenderRequest(
        template="{{ x }}",
        data="x: 1",
        render_mode="bogus",
    )
    with pytest.raises(ValueError, match="Unknown render mode"):
        e.render(req)


def test_normal_render_still_works():
    """Subprocess round-trip produces the correct output for a simple template."""
    e = _engine()
    req = RenderRequest(
        template="hello {{ name }}",
        data="name: world",
        render_mode="base",
    )
    assert e.render(req) == "hello world"
