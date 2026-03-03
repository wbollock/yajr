# Jinja Parser Clone Plan

## Goals
- Clone core UX of https://j2live.ttl255.com/.
- Use one shared rendering core for both CLI and web.
- Add stateless sharing (no server persistence).
- Prioritize security for untrusted templates.
- Build with TDD.

## Architecture
- Language: Python 3.9+.
- Core package: `src/jinja_parser/core`.
- CLI entrypoint: `jinja-render`.
- Web API/UI: FastAPI (`src/jinja_parser/web/app.py`) + static frontend in `web/`.

### Shared Core
- `RenderRequest` model carries template/data/options/mode/filters.
- `parse_data_blob` supports YAML and JSON mapping input.
- `RenderEngine` handles rendering by mode.
- `ShareCodec` creates signed, compressed share tokens.

### Security Model
- Base mode uses Jinja `SandboxedEnvironment`.
- Undefined behavior configurable with strict mode.
- Share links are stateless tokens; nothing is written to DB.
- Token integrity is protected with HMAC.

## API
- `POST /api/render`: render template, return `render_result`.
- `POST /api/share`: return signed share token and URL.
- `GET /api/share/{token}`: decode payload from token.
- `GET /`: app UI.
- `GET /s/{token}`: app UI preloaded from token.
- `GET /healthz`: health check.

## TDD Plan
1. Core parsing/render tests.
2. Security regression tests for common SSTI/RCE patterns.
3. Share codec tests for token roundtrip.
4. API tests for render/share flows.
5. CLI integration test.

## Mode Compatibility Plan
- `base`: implemented via sandboxed Jinja2.
- `ansible`: implement adapter backed by `ansible-core` templating runtime and add golden tests.
- `salt`: implement adapter backed by Salt renderer and add golden tests.

## Constraints and Tradeoffs
- "100% compatibility" for Ansible/Salt requires those runtimes and pinned versions.
- Secure-by-default web mode may intentionally block dangerous constructs.
- Stateless share links get longer as payload grows.

## Conventional Commit Milestones
- `feat(core): add shared render engine and parser`
- `feat(web): add fastapi render/share endpoints and clone UI`
- `feat(cli): add shared-core CLI renderer`
- `test(core): add rendering and security coverage`
- `docs(plan): capture architecture and security model`
