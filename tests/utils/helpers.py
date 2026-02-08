import json
from pathlib import Path

import pytest
from dash._utils import AttributeDict
from dash.development.base_component import Component
from flash import Flash

from flash_router import FlashRouter
from flash_router.core.routing import PageNode, RouteTable, RouteTree
from flash_router.utils.helper_functions import format_relative_path


def serialize_value(value):
    if isinstance(value, PageNode):
        return value.model_dump(
            mode="python",
            exclude={"layout", "loading", "error", "endpoint"},
        )
    if isinstance(value, Component):
        return f"<{value.__class__.__name__}>"
    if callable(value):
        name = getattr(value, "__name__", value.__class__.__name__)
        module = getattr(value, "__module__", "unknown")
        return f"<callable {module}.{name}>"
    if isinstance(value, dict):
        return {key: serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_value(item) for item in value]
    return value


def serialize_route_table():
    return {key: serialize_value(node) for key, node in RouteTable._table.items()}


def serialize_route_tree():
    dynamic_routes = RouteTree._dynamic_routes
    return serialize_value(
        {
            "static": RouteTree._static_routes,
            "dynamic": {
                "routes": {
                    segment: RouteTable.get_node(node_id)
                    for segment, node_id in dynamic_routes.routes.items()
                },
                "path_template": RouteTable.get_node(dynamic_routes.path_template)
                if dynamic_routes.path_template
                else None,
            },
        }
    )


def store_route_table(path: str = "tests/utils/route_table.json") -> None:
    with open(path, "w+", encoding="utf-8") as file:
        json.dump(serialize_route_table(), file, indent=2, sort_keys=True)


def store_route_tree(path: str = "tests/utils/route_tree.json") -> None:
    with open(path, "w+", encoding="utf-8") as file:
        json.dump(serialize_route_tree(), file, indent=2, sort_keys=True)


def get_leaf_node(exec_node):
    current = exec_node
    while current and current.child_node and current.child_node != "default":
        current = current.child_node
    return current


def done_state(node, next_segment):
    segment_key = node.create_segment_key(next_segment)
    return segment_key, {"state": "done", "node_id": node.node_id}


def get_node_by_path(path):
    formatted_path = format_relative_path(path)
    for node in RouteTable._table.values():
        if node.path == formatted_path:
            return node
    return None


@pytest.fixture(autouse=True)
def reset_route_state():
    RouteTable._table = {}
    RouteTree._static_routes = {}
    RouteTree._dynamic_routes = AttributeDict(routes={}, path_template=None)
    yield


@pytest.fixture()
def router():
    pages_dir = Path(__file__).resolve().parents[1] / "pages"
    app = Flash(
        __name__,
        prevent_initial_callbacks=True,
        pages_folder=str(pages_dir),
        use_pages=False,
    )
    return FlashRouter(app)
