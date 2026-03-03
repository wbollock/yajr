from fastapi.testclient import TestClient

from jinja_parser.web.app import create_app


def test_render_endpoint_works():
    client = TestClient(create_app(secret="test-secret"))
    response = client.post(
        "/api/render",
        json={
            "template": "hello {{ name }}",
            "data": "name: world",
            "render_mode": "base",
            "options": {"strict": False, "trim": False, "lstrip": False},
            "filters": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["render_result"] == "hello world"


def test_share_endpoint_roundtrip_without_db():
    client = TestClient(create_app(secret="test-secret"))
    payload = {
        "template": "{{ x }}",
        "data": "x: 7",
        "render_mode": "base",
        "options": {"strict": True, "trim": False, "lstrip": False},
        "filters": ["hash", "ipaddr"],
    }

    share_response = client.post("/api/share", json=payload)
    assert share_response.status_code == 200
    token = share_response.json()["token"]

    view_response = client.get(f"/api/share/{token}")
    assert view_response.status_code == 200
    assert view_response.json() == payload
