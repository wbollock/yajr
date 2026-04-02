import json
import re
from typing import Any, Dict

import yaml

# Matches any run of leading whitespace that contains at least one tab —
# covers pure-tab prefixes ("\t\t") and mixed prefixes (" \t", "\t ") alike.
_INDENT_WITH_TAB = re.compile(r"^[ \t]*\t[ \t]*", re.MULTILINE)


def parse_data_blob(data_blob: str) -> Dict[str, Any]:
    data_blob = data_blob or ""
    if not data_blob.strip():
        return {}

    # YAML forbids tab characters in indentation. Expand tabs only inside
    # leading whitespace so mid-line tabs (e.g. inside JSON string values)
    # are left intact.
    data_blob = _INDENT_WITH_TAB.sub(lambda m: m.group().expandtabs(4), data_blob)

    try:
        loaded = json.loads(data_blob)
    except json.JSONDecodeError:
        try:
            loaded = yaml.safe_load(data_blob)
        except yaml.YAMLError as exc:
            raise ValueError(f"Data parse error: {exc}") from exc

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("Input data must be a JSON/YAML mapping object.")
    return loaded

