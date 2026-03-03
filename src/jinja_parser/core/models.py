from dataclasses import dataclass, field
from typing import Dict, List


MODE_ALIASES = {
    "base": "base",
    "rmode_base": "base",
    "ansible": "ansible",
    "rmode_ansible": "ansible",
    "salt": "salt",
    "rmode_salt": "salt",
}


@dataclass
class RenderRequest:
    template: str
    data: str
    render_mode: str = "base"
    options: Dict[str, bool] = field(default_factory=dict)
    filters: List[str] = field(default_factory=list)

    def normalized_mode(self) -> str:
        mode = MODE_ALIASES.get(self.render_mode)
        if mode is None:
            raise ValueError(f"Unknown render mode: {self.render_mode}")
        return mode

