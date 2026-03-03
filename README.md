# jinja_parser

Secure J2Live-style Jinja renderer with:
- Shared rendering core for CLI and web
- Stateless share links (signed + compressed token)
- TDD-backed behavior

## Quick start
```bash
python3 -m pip install -e '.[dev]'
pytest -q
uvicorn jinja_parser.web.app:app --reload
```

## CLI
```bash
jinja-render --mode base --template-file template.j2 --data-file data.yml
```

## Security notes
- Base rendering uses `jinja2.sandbox.SandboxedEnvironment`.
- Template/share payloads are not persisted in a database.
- Share links are self-contained tokens signed with `JINJA_SHARE_SECRET`.

## Status
- Base Jinja mode: implemented.
- Ansible mode: implemented via `ansible-core` templating runtime.
- Salt mode: implemented via Salt Jinja renderer.
- UI includes a `Load defaults` button for starter template/data.
