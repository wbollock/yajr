from jinja_parser.core.models import RenderRequest
from jinja_parser.core.share import ShareCodec


def test_encode_decode_roundtrip():
    codec = ShareCodec(secret="test-secret")
    req = RenderRequest(
        template="hello {{ who }}",
        data="who: team",
        render_mode="base",
        options={"strict": True, "trim": True, "lstrip": False},
        filters=["hash"],
    )

    token = codec.encode(req)
    restored = codec.decode(token)

    assert restored.template == req.template
    assert restored.data == req.data
    assert restored.render_mode == req.render_mode
    assert restored.options == req.options
    assert restored.filters == req.filters
