import json
from dataclasses import dataclass
from typing import Any

from dash import dcc, html

type ContainerId = str | dict[str, str]

# Shared `type` key for all router container dictionary IDs.
CONTAINER_TYPE = "DASH-ROUTER-CONTAINER"
# Separate `type` key for deferred lazy boundaries so `Output(ALL)` never overlaps with `Output(MATCH)`.
LAZY_TYPE = "DASH-ROUTER-LAZY"


def container_key(container_id: ContainerId) -> str:
    """Stable string form of a container id, for sets and dict keys."""
    return json.dumps(container_id, sort_keys=True)


@dataclass
class ContainerProps:
    # URL segment of the child rendered inside (e.g. "timeline"), or `None`.
    active: str | None = None
    # Browser path of the parent node (e.g. "/orders/1003"); child URLs are `f"{base}/{segment}"`.
    base: str | None = None


class ChildContainer(html.Div):
    class ids:
        @staticmethod
        def container(parent_id: str) -> dict[str, str]:
            return {"type": CONTAINER_TYPE, "index": f"{parent_id}-children"}

    props: ContainerProps

    def __init__(
        self,
        layout: Any = None,
        parent_id: str = "/",
        active: str | None = None,
        base: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.props = ContainerProps(active=active, base=base)
        super().__init__(children=layout, id=self.ids.container(parent_id), disable_n_clicks=True, **kwargs)


class SlotContainer(html.Div):
    class ids:
        @staticmethod
        def container(parent_id: str, slot_name: str) -> dict[str, str]:
            return {"type": CONTAINER_TYPE, "index": f"{parent_id}-slot-{slot_name.strip('()')}"}

    def __init__(self, layout: Any = None, parent_id: str = "/", slot_name: str = "", **kwargs: Any) -> None:
        super().__init__(children=layout, id=self.ids.container(parent_id, slot_name), disable_n_clicks=True, **kwargs)


class LazyContainer(html.Div):
    class ids:
        @staticmethod
        def container(lazy_key: str) -> dict[str, str]:
            return {"type": LAZY_TYPE, "index": lazy_key}

    def __init__(
        self,
        layout: Any = None,
        lazy_key: str = "",
        *,
        route: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        extra_props: dict[str, Any] = {"data-route": json.dumps(route, separators=(",", ":"), sort_keys=True)} if route is not None else {}
        super().__init__(children=layout, id=self.ids.container(lazy_key), disable_n_clicks=True, **extra_props, **kwargs)


class RootContainer(html.Div):
    class ids:
        wrapper = "dash-router-root"
        container = {"type": CONTAINER_TYPE, "index": "root"}
        location = "dash-router-location"
        committed_store = "dash-router-committed-store"

    def __init__(self, initial_children: Any = None, **kwargs: Any) -> None:
        super().__init__(
            [
                dcc.Location(id=self.ids.location, refresh="callback-nav"),
                html.Div(children=initial_children, id=self.ids.container, disable_n_clicks=True),
                dcc.Store(id=self.ids.committed_store, data=None),
            ],
            id=self.ids.wrapper,
            disable_n_clicks=True,
            **kwargs,
        )
