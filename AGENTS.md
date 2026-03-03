# AGENTS.md

## Project intent
Build a secure J2Live-style renderer with shared core logic used by both CLI and web.

## Engineering rules
- Follow TDD: add or update tests before behavior changes.
- Keep CLI and web rendering behavior aligned through `jinja_parser.core` only.
- Never add persistent storage for template/share content unless explicitly requested.
- Treat template input as untrusted; preserve sandboxed execution semantics.

## Commit style
- Use Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`).
- Keep changes scoped and small when possible.

## Test commands
- `pytest -q`

## Run commands
- CLI: `jinja-render --mode base --template-file template.j2 --data-file data.yml`
- Web: `uvicorn jinja_parser.web.app:app --reload`
