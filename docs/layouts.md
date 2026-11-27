# Layouts and containers

## What a layout can be

The function or component a route file defines, named after the file (`page`, `loading`, `error`, `default`; see [Naming](routing.md#naming)), can be:

- a component: `page = html.H1("Settings")`
- a function: `def page(**_): ...`
- an async function: `async def page(**_): ...`

A function is called every time its node renders. A component is reused as is.

## What a layout receives

The router calls a layout function with keyword arguments:

| Argument | Type | Present when |
| --- | --- | --- |
| `children` | `ChildContainer` | The node has child routes (or takes `children`). Holds the active child. |
| one argument per slot, named after the slot | `SlotContainer` | The node has `(slot)` folders. `(kpis)/` arrives as `kpis`. |
| `data` | anything | The node has an `api.py`: its return value, else `None`. |
| path variables | coerced from the annotation | For its own `[param]` and every ancestor's. |
| query values | coerced from the annotation | Every query parameter of the URL. |
| a Pydantic model argument | your model | Built from the query string ([details](query-params.md#pydantic-query-models)). |

```python
# pages/overview/page.py
from dash import html

from dash_router import SlotContainer


def page(kpis: SlotContainer, revenue: SlotContainer, range: str = "30d", **_):
    return html.Div([html.H1(f"Overview ({range})"), kpis, revenue])
```

The router inspects each signature once, at startup:

- Arguments named `children`, `data` or after a slot are filled by the router. They never count as query parameters.
- Any other argument with a plain type (`str`, `int`, `float`, `bool`, an `Enum`, `Literal`, `list[...]`, or untyped) is a **query parameter**. The node subscribes to it: when it changes, the node re-renders ([details](query-params.md#subscriptions-who-re-renders)).
- Without `**kwargs`, the router passes only the arguments the function declares. With `**kwargs`, it passes everything above.

End every layout with `**_`. It keeps the function working when the router has more to pass than you need.

## Rule 1: always render the containers you receive

The router patches `children` and slot containers in place on later navigations, without calling the parent layout again. If a layout does not put a container in its output, a later navigation has nothing to patch, and that part of the page never appears.

Wrong: the container is only rendered in some cases.

```python
def page(inspector: SlotContainer, **_):
    if inspector.children is None:
        return html.P("Select a customer.")  # the slot container is gone
    return html.Div(inspector)
```

Right: always render it, and show the placeholder next to it.

```python
def page(inspector: SlotContainer, **_):
    hint = html.P("Select a customer.", className="slot-hint")
    return html.Div([inspector, hint], className="slot-children")
```

```css
/* show the hint only while the container is empty */
.slot-hint { display: none; }
.slot-children > div:empty + .slot-hint { display: block; }
```

The showcase uses exactly this for its customer inspector (`pages/customers/(inspector)/page.py`).

## Rule 2: a layout only runs when its node renders

A parent layout is not called again when a child or a sibling slot changes. Do not compute something in a parent from a value that only its children subscribe to. Put the logic in the node that subscribes, or let the parent subscribe too by declaring the parameter.

## Reading the active child

`children.props.active` is the URL segment of the active child (`"summary"`, `"timeline"`, ...). `UrlSegment` uses it to choose the initial tab, then keeps the tab in sync with the URL in both directions with no callback:

```python
from dash_router import ChildContainer, RouteConfig, UrlSegment

config = RouteConfig(default_child="summary")


def page(children: ChildContainer, **_):
    tabs = UrlSegment(
        dmc.Tabs(
            dmc.TabsList([dmc.TabsTab("Summary", value="summary"), dmc.TabsTab("Timeline", value="timeline")]),
            id="order-tabs",
        ),
        children,
        default="summary",  # the bare URL /orders/1003 stands for the summary tab
    )
    return html.Div([tabs, children])
```

Clicking a tab pushes `/orders/1003/timeline` (or `/orders/1003` for the default). Back and forward select the tab again. The parent layout does not re-render when only the child changes, which is why the tabs need `UrlSegment` (or a callback) to follow the URL. [Navigation](navigation.md#tabs-in-the-url-urlsegment) describes it in detail.

## Container ids

Every container has a predictable id, useful in tests and in callbacks that need to target a part of the page:

| Container | Id |
| --- | --- |
| Child of node `orders` | `ChildContainer.ids.container("orders")` -> `{"type": "DASH-ROUTER-CONTAINER", "index": "orders-children"}` |
| Slot `kpis` of node `overview` | `SlotContainer.ids.container("overview", "kpis")` -> `{"type": "DASH-ROUTER-CONTAINER", "index": "overview-slot-kpis"}` |
| The whole page | `RootContainer.ids.container` -> `{"type": "DASH-ROUTER-CONTAINER", "index": "root"}` |

All containers share one id `type` (`"DASH-ROUTER-CONTAINER"`); the router updates each container's `children` directly via `set_props`.

The router owns the `children` of these containers. Do not write to them from your own callbacks.

## Callbacks inside routes

Define callbacks with `@callback` (or `clientside_callback`) in `page.py`, or in a `callbacks.py` / `callback.py` next to it. The router imports these files when it builds the tree, so the callbacks are registered before the app starts.

- Component ids must be unique among everything mounted at the same time. A slot and the main branch may be on screen together.
- Initial calls work as on a normal dynamic Dash update. When routed content mounts (including streamed `loading.py` / generator layouts), Dash runs the callbacks whose `Output`s are in it, unless they set `prevent_initial_call=True`.
- Note: callbacks without any `Output` (callbacks that only use `set_props`) do not run an initial call on dynamic mount, matching stock Dash. Use an `Output` if the callback should run automatically when the route mounts.

## Imports inside route folders

Route folders are registered as Python packages, even when their names are not valid identifiers (`(kpis)`, `[order_id]`). Relative imports work:

```python
# pages/orders/(listing)/api.py
from ..models import PAGE_SIZE, OrderFilters  # pages/orders/models.py
```

Shared modules outside `pages/` (for example `ui.py`, `data.py`) can be imported normally as long as their folder is on `sys.path`. The showcase adds its own folder to `sys.path` in `app.py`.
