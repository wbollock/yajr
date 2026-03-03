# YAJR (jinja_parser)

Secure YAJR (Yet Another Jinja Renderer) with:
- Shared rendering core for CLI and web
- Short share links with server-side slug storage
- TDD-backed behavior

## Quick start
```bash
python3 -m pip install -e '.[dev]'
pytest -q
uvicorn jinja_parser.web.app:app --reload
```

## Reproducible deps
```bash
python3 -m pip install -r requirements.lock.txt
```

## UI E2E tests
```bash
python3 -m playwright install chromium
pytest -q tests/test_e2e_ui.py
```

## CLI
```bash
jinja-render --mode base --template-file template.j2 --data-file data.yml
```

## Security notes
- Base rendering uses `jinja2.sandbox.SandboxedEnvironment`.
- Share links are compact slugs stored in app memory.
- Configure `JINJA_SHARE_SECRET` in deployment for other security-sensitive settings.

## Status
- Base Jinja mode: implemented.
- Ansible mode: implemented via `ansible-core` templating runtime.
- Salt mode: implemented via Salt Jinja renderer.
- UI includes a `Load defaults` button for starter template/data.
