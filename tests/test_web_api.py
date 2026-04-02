from fastapi.testclient import TestClient

from jinja_parser.web.app import MAX_DATA_CHARS, MAX_TEMPLATE_CHARS, create_app


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


def test_share_endpoint_roundtrip_short_slug():
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

    assert len(token) <= 10
    assert share_response.json()["share_url"].endswith(f"/s/{token}")

    view_response = client.get(f"/api/share/{token}")
    assert view_response.status_code == 200
    assert view_response.json() == payload


def test_index_contains_runtime_versions_label():
    client = TestClient(create_app(secret="test-secret"))
    response = client.get("/")
    assert response.status_code == 200
    assert "Runtime support" in response.text


def test_render_rejects_oversized_template():
    client = TestClient(create_app(secret="test-secret"))
    response = client.post(
        "/api/render",
        json={
            "template": "x" * (MAX_TEMPLATE_CHARS + 1),
            "data": "{}",
            "render_mode": "base",
            "options": {"strict": False, "trim": False, "lstrip": False},
            "filters": [],
        },
    )
    assert response.status_code == 422


def test_render_endpoint_accepts_tab_indented_yaml():
    """Tab-indented YAML data must render successfully via the web API."""
    client = TestClient(create_app(secret="test-secret"))
    response = client.post(
        "/api/render",
        json={
            "template": "{{ secret.token }}",
            "data": "secret:\n\ttoken: abc",
            "render_mode": "base",
            "options": {"strict": False, "trim": False, "lstrip": False},
            "filters": [],
        },
    )
    assert response.status_code == 200
    assert response.json()["render_result"] == "abc"


def test_render_strict_mode_reports_undefined_variable():
    """strict mode with an undefined variable returns 200 with an error string in the result."""
    client = TestClient(create_app(secret="test-secret"))
    response = client.post(
        "/api/render",
        json={
            "template": "{{ missing }}",
            "data": "x: 1",
            "render_mode": "base",
            "options": {"strict": True, "trim": False, "lstrip": False},
            "filters": [],
        },
    )
    assert response.status_code == 200
    assert "Rendering error" in response.json()["render_result"]


def test_render_invalid_yaml_data_returns_422():
    """Malformed data that is neither JSON nor YAML returns 422 with a JSON detail message."""
    client = TestClient(create_app(secret="test-secret"))
    response = client.post(
        "/api/render",
        json={
            "template": "{{ x }}",
            "data": "{unclosed: brace",
            "render_mode": "base",
            "options": {"strict": False, "trim": False, "lstrip": False},
            "filters": [],
        },
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_render_inconsistent_yaml_indentation_returns_422():
    """YAML with inconsistent indentation returns 422, not a raw 500 that breaks the browser."""
    client = TestClient(create_app(secret="test-secret"))
    data = "secret:\n    linode_token: \"123\"\n     region: \"us-east-1\""
    response = client.post(
        "/api/render",
        json={
            "template": "{{ secret.linode_token }}",
            "data": data,
            "render_mode": "base",
            "options": {"strict": False, "trim": False, "lstrip": False},
            "filters": [],
        },
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_render_rejects_oversized_data():
    client = TestClient(create_app(secret="test-secret"))
    response = client.post(
        "/api/render",
        json={
            "template": "{{ x }}",
            "data": "x" * (MAX_DATA_CHARS + 1),
            "render_mode": "base",
            "options": {"strict": False, "trim": False, "lstrip": False},
            "filters": [],
        },
    )
    assert response.status_code == 422
