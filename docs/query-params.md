# Query parameters

Query parameters are ordinary function arguments. The router reads the signature of each route function (`page`, `layout`, ...) and `endpoint`, parses the query string, coerces the values to the annotated types and passes them in.

```python
# pages/overview/(revenue)/api.py
from .models import Range  # class Range(str, Enum): D7 = "7d"; D30 = "30d"; D90 = "90d"


async def endpoint(range: Range = Range.D30, **_):
    return await revenue_series(range.days)  # ?range=7d -> Range.D7
```

## Which arguments are query parameters

An argument of a route function or `endpoint` is a query parameter when:

- it is not `children`, `data` or the name of one of the node's slots, and
- its annotation is a plain type: `str`, `int`, `float`, `bool`, an `Enum`, a `Literal[...]`, a generic such as `list[str]`, any of these with `| None`, or no annotation at all.

Arguments annotated with a component or container type are ignored. An argument annotated with a Pydantic model turns every field of the model into a query parameter ([below](#pydantic-query-models)).

If a query parameter has the same name as a path variable, the path variable wins.

## Coercion and defaults

| Signature | URL | Value |
| --- | --- | --- |
| `page: int = 1` | `?page=3` | `3` |
| `page: int = 1` | no `page` | `1` |
| `range: Range = Range.D30` | `?range=7d` | `Range.D7` |
| `archived: bool = False` | `?archived=true` | `True` |
| `tag: list[str] \| None = None` | `?tag=a,b` | `["a", "b"]` |
| `tag: list[str] \| None = None` | `?tag=a&tag=b` | `["a", "b"]` |
| `tag: list[str] \| None = None` | `?tag=a` | `["a"]` |
| `q` (no annotation) | `?q=berg` | `"berg"` |

- Lists are written comma separated (`?tag=a,b`). This is the format `UrlParam` and `Url.to_href()` write. Repeated keys (`?tag=a&tag=b`) are accepted too. A list-typed parameter with a single value gets a one-item list.
- A value that does not validate (`?page=abc` for `page: int`) makes the layout or endpoint raise. The node's error boundary then renders ([error.py](data-loading.md#errorpy-error-boundaries)).

## Subscriptions: who re-renders

The query parameters of a node (from its route function and its `endpoint` together) are its **subscriptions**. On a navigation that changes only the query string, the router compares each node's subscribed values before and after, and re-renders only the nodes whose values changed, together with everything inside them.

```text
/overview  ->  /overview?range=7d
```

Only `(revenue)` declares `range`, so only the Revenue slot re-renders. The page, the shell and the other slots keep their content. Their `rendered` badges in the showcase do not change.

Values are compared **after** coercion and defaults:

- `?page=1` and no `page` are the same when the default is `1`, so adding `?page=1` re-renders nothing.
- `?range=7d` and `?range=7d&utm=x` are the same for a node that does not declare `utm`.

`**kwargs` still receives every query value, but it subscribes to nothing. A node that reads `kwargs["status"]` will not re-render when `status` changes. Declare every parameter you rely on.

## Pydantic query models

Group related parameters into a model:

```python
# pages/orders/models.py
from pydantic import BaseModel, Field


class OrderFilters(BaseModel):
    status: OrderStatus = OrderStatus.ALL
    q: str = ""
    page: int = Field(default=1, ge=1)
```

```python
# pages/orders/(listing)/api.py
from ..models import PAGE_SIZE, OrderFilters


async def endpoint(filters: OrderFilters, **_):
    rows = await search_orders(filters.status, filters.q)
    start = (filters.page - 1) * PAGE_SIZE
    return {"rows": rows[start : start + PAGE_SIZE], "total": len(rows)}
```

- `?status=delayed&q=berg&page=2` arrives as `OrderFilters(status=OrderStatus.DELAYED, q="berg", page=2)`.
- Each field (`status`, `q`, `page`) is a subscription of the node. The field defaults count as the values of omitted parameters.
- The model's validation applies. `?page=0` fails `ge=1`, and the node's error boundary renders.
- The argument name (`filters`) is not part of the URL.

In the showcase, the order list (`(listing)`) subscribes to the filters and the order detail does not. Selecting another order keeps the list as it is. Changing a filter re-renders only the list.

## Changing the query string

A query change is a normal navigation. Build links or callback URLs with `url_for` (passing query arguments or a Pydantic query model directly), or edit the current URL with `get_current_url()`:

```python
from dash_router import Link, get_current_url, navigate, url_for

# Link to a route with typed query parameters (or a Pydantic query model)
Link("Delayed orders", url_for("orders", status=OrderStatus.DELAYED, page=1))
Link("Order #1003", url_for("orders/[order_id]", filters, order_id=1003))


# Edit the current page's query string from a callback
@callback(Input("range-select", "value"), prevent_initial_call=True)
def set_range(value):
    navigate(get_current_url().set_param("range", value))


# Or navigate to another route with query parameters
@callback(Input("view-delayed", "n_clicks"), prevent_initial_call=True)
def open_delayed(n_clicks):
    navigate(url_for("orders", status=OrderStatus.DELAYED))
```

See [Navigation](navigation.md) for `url_for` and `Url`.

## UrlParam and UrlCommit

`UrlParam` syncs one prop of a component with a query parameter, in the browser. `UrlCommit` writes the values of a group when its component fires. Neither needs a callback:

```python
import dash_mantine_components as dmc

from dash_router import UrlParam

UrlParam(
    dmc.SegmentedControl(id="range", data=["7d", "30d", "90d"], value="30d"),
    param="range",
    default="30d",
    two_way=True,
)
```

Changing the control writes `?range=7d`. That is a normal navigation, so the router re-renders the slot that subscribes to `range`. With `two_way=True` the control also follows the URL on back and forward. Without it, the layout renders the value from the URL on the server and the control is not updated later.

- `prop` is the prop that is synced (default `"value"`).
- `default` is the value the parameter stands for when it is missing. While the control has that value, the parameter is left out of the URL. Pass it for every parameter whose default is not empty (`None`, `""` or `[]`). Otherwise a page opened with `?page=1` cannot tell the default apart and writes it.
- `clear=["page"]` removes other parameters whenever this one changes, for example a new filter resets the page.
- `format` sets how the value is written: `"auto"` (inferred from the value), `"string"`, `"list"`, `"number"`, `"boolean"` or `"json"`. Lists are comma separated: `?status=open,closed`.
- `history="replace"` changes the URL without adding a history entry. `debounce=400` waits that many milliseconds after the last change, for example for a search box.

Writes are batched, so several changes in the same tick become one history entry. They go through the browser's `pushState`, which the router's location picks up, so they start the same navigation as a link.

Several controls can be committed together with a group. Their values are written only when a `UrlCommit` with the same group is clicked:

```python
from dash_router import UrlCommit, UrlParam

UrlParam(dmc.TextInput(id="search"), param="q", group="filters", default="")
UrlParam(dmc.Select(id="status", data=["all", "open", "shipped"], value="all"), param="status", group="filters", default="all")
UrlCommit(dmc.Button("Apply", id="apply"), group="filters", clear=["page"])
```

- A `UrlCommit` with a `group` writes the values of that group. Its `set_params` are written only if at least one parameter of the group has a value, otherwise those keys are removed.
- A `UrlCommit` without a group always writes its `set_params`. Use it for buttons that set fixed values, such as a next-page button: `UrlCommit(dmc.Button("Next"), set_params={"page": "2"})`.
- The `prop` of `UrlCommit` that triggers the write is `n_clicks` by default.

The full signatures are in the [API reference](api-reference.md#components).

## Extra routing inputs

Besides the URL, the router can pass values from other components to your layouts. Set `app.routing_callback_inputs` **before** creating the router:

```python
from dash import State

app.routing_callback_inputs = {"tenant": State("tenant-store", "data")}
router = DashRouter(app, pages_folder="pages")
```

```python
def page(tenant: str | None = None, **_):
    ...
```

- The values are read on every navigation and merged with the query parameters. A key that is also in the query string takes the value from the component.
- Nodes subscribe to them like query parameters. A node that declares `tenant` re-renders on the next navigation if the value differs from the previous one.
- Use `State`, not `Input`: the router reads the values when the URL changes and does not watch the components.

In tests, pass them as `extra_inputs=` / `prev_extra_inputs=` ([Testing routes](testing.md)).
