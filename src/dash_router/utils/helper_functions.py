import json
from typing import Any

from dash._utils import to_json


def recursive_to_plotly_json(component: Any) -> Any:
    """Convert any Dash component, list, dict, or scalar into a JSON-compatible Python structure."""
    if component is None or isinstance(component, str | int | float | bool):
        return component
    serialized = to_json(component)
    return json.loads(serialized) if isinstance(serialized, str) else serialized
