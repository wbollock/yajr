# YAJR (jinja_parser)

YAJR (Yet Another Jinja Renderer) with:
- Shared rendering core for CLI and web
- Short share links with server-side slug storage
- TDD-backed behavior

## Quick start
## Mise workflow
```bash
mise install
mise run install
mise run test
mise run run
```

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
- All rendering runs in a sandboxed subprocess with a hard CPU-time limit
  (`RLIMIT_CPU = 5 s`), an 8-second wall-clock timeout, a 1 MB output cap,
  and outbound network access blocked.
- Base mode uses `jinja2.sandbox.SandboxedEnvironment`.  Ansible mode upgrades
  Ansible's Jinja environment to the same sandboxed class before any template
  is compiled.  Salt mode points `file_roots` / `pillar_roots` at an empty
  directory to prevent `salt://` reads of the host filesystem.
- These controls are best-effort hardening, not a hard security boundary.
  See [Jinja's own sandbox caveat](https://jinja.palletsprojects.com/en/stable/sandbox/).
  Do not put sensitive data in templates or input.
- Share links are compact slugs stored in a SQLite database (`:memory:` by
  default; set `YAJR_SHARE_DB=/data/shares.db` for persistence).
- Share links do **not** auto-render on page load — the user must click Render.

## Status
- Base Jinja mode: implemented.
- Ansible mode: implemented via `ansible-core` templating runtime.
- Salt mode: implemented via Salt Jinja renderer.
- UI includes a `Load defaults` button for starter template/data.
