import argparse
import sys
from pathlib import Path

from .core.models import RenderRequest
from .core.renderer import RenderEngine


def _read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Jinja templates safely.")
    parser.add_argument("--mode", default="base", choices=["base", "ansible", "salt"])
    parser.add_argument("--template-file", required=True)
    parser.add_argument("--data-file", required=True)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--trim", action="store_true")
    parser.add_argument("--lstrip", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    req = RenderRequest(
        template=_read_text(args.template_file),
        data=_read_text(args.data_file),
        render_mode=args.mode,
        options={"strict": args.strict, "trim": args.trim, "lstrip": args.lstrip},
        filters=[],
    )
    output = RenderEngine().render(req)
    sys.stdout.write(output)
    if not output.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

