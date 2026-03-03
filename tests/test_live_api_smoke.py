import os

import pytest
import requests


BASE_URL = os.environ.get("YAJR_BASE_URL")


@pytest.mark.skipif(not BASE_URL, reason="Set YAJR_BASE_URL to run live API smoke tests")
def test_live_render_modes_smoke():
    cases = [
        {
            "mode": "base",
            "template": "hello {{ name }}",
            "data": "name: world",
        },
        {
            "mode": "ansible",
            "template": "{{ {'eth0': 'up', 'eth1': 'down'} | dict2items | length }}",
            "data": "{}",
        },
        {
            "mode": "salt",
            "template": "{{ {'x': 1} | json }}",
            "data": "{}",
        },
    ]

    for c in cases:
        resp = requests.post(
            f"{BASE_URL}/api/render",
            json={
                "template": c["template"],
                "data": c["data"],
                "render_mode": c["mode"],
                "options": {"strict": True, "trim": True, "lstrip": True},
                "filters": [],
            },
            timeout=8,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert "render_result" in payload
        assert not payload["render_result"].startswith("Rendering error:"), (
            c["mode"],
            payload["render_result"],
        )
