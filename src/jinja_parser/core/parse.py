import json
import re
from typing import Any, Dict

import yaml

_LEADING_TABS = re.compile(r"^(\t+)", re.MULTILINE)


def parse_data_blob(data_blob: str) -> Dict[str, Any]:
    data_blob = data_blob or ""
    if not data_blob.strip():
        return {}

    # YAML forbids tab characters for indentation; replace leading tabs on
    # each line with spaces so tab-indented input parses correctly.
    # Only leading tabs are replaced so mid-line tabs (e.g. inside JSON string
    # values) are left intact.
    data_blob = _LEADING_TABS.sub(lambda m: "    " * len(m.group(1)), data_blob)

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

