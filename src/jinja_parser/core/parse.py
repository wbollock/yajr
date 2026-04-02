import json
from typing import Any, Dict

import yaml


def parse_data_blob(data_blob: str) -> Dict[str, Any]:
    data_blob = data_blob or ""
    if not data_blob.strip():
        return {}

    # YAML forbids tab characters for indentation; expand to spaces so
    # tab-indented input (common from editors/copy-paste) parses correctly.
    data_blob = data_blob.expandtabs(4)

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

