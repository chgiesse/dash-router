import json

from dash.development.base_component import Component
from flash_router.core.routing import PageNode, RouteTable, RouteTree


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
