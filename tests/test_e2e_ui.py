import socket
import subprocess
import time
from contextlib import closing

import pytest

playwright = pytest.importorskip("playwright.sync_api")


def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for {host}:{port}")


@pytest.fixture(scope="module")
def live_server():
    proc = subprocess.Popen(
        [
            "uvicorn",
            "jinja_parser.web.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8123",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_port("127.0.0.1", 8123)
        yield "http://127.0.0.1:8123"
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_ui_buttons_and_share_flow(live_server):
    try:
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.click("#load_defaults")
            page.click("#request_render")

            expect = playwright.expect
            expect(page.locator("#render_results")).to_contain_text("interface Ethernet1")

            page.click("#toggle_whitespaces")
            expect(page.locator("#render_results .ws_vis").first).to_be_visible()

            page.click("#create_share")
            share_url = page.locator("#share_url").input_value()
            assert share_url.startswith(f"{live_server}/s/")

            page.click("#reset_render")
            expect(page.locator("#render_results")).to_have_text("")

            page.goto(share_url)
            expect(page.locator("#render_results")).to_contain_text("interface Ethernet1")

            page.click("#theme_toggle")
            assert page.locator("body").get_attribute("data-theme") == "light"

            browser.close()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Playwright/browser unavailable in this environment: {exc}")
