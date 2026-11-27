# Navigation

Every navigation, whatever triggered it, goes through the router's `dcc.Location` (`RootContainer.ids.location`). The router compares the new URL with the previous one and renders only the difference ([Transitions](transitions.md)). Back and forward buttons work the same way.

## Links

`dash_router.Link` changes the URL without reloading the page and marks itself as active:

```python
from dash_router import Link

Link("Orders", href="/orders")                     # active on /orders and /orders/...
Link("Overview", href="/overview", match="exact")  # active on /overview only
Link("Orders", href="/orders", replace=True)       # replace the history entry instead of adding one
```

The active link gets `aria-current="page"` and `data-active="true"`, so you can style it. It reads the browser's URL itself, so it stays correct in a persistent shell that the router does not re-render, such as a header or a sidebar. Ctrl/Cmd and middle clicks, a `target` other than `_self`, and links to another origin are left to the browser.

Other components also change the URL without a reload:

```python
from dash import dcc
import dash_mantine_components as dmc

dcc.Link("Orders", href="/orders")
dmc.Anchor("Order 1003", href="/orders/1003")
dmc.NavLink(label="Customers", href="/customers", active="partial")
```

`dmc.NavLink(active="partial" | "exact" | "exact-with-search")` also follows the router's location by itself, so a sidebar of NavLinks in a persistent shell needs no callback to highlight the current page.

A plain `html.A(href=...)` reloads the whole page. It still works, but you lose the persistent shell and the partial update.

## Tabs in the URL: `UrlSegment`

`UrlSegment` binds one prop of a component (`value` of `dmc.Tabs` by default) to the URL segment after a base path. It needs no callback:

```python
from dash_router import ChildContainer, RouteConfig, UrlSegment

config = RouteConfig(default_child="summary")


def page(children: ChildContainer, order_id: int, **_):
    tabs = UrlSegment(order_tabs(), children, default="summary")
    return dmc.Card([tabs, dmc.Box(children)])
```

- `children` is the `ChildContainer` of the page. Its `props.base` is the browser path of the parent (`/orders/1003`), and `props.active` is the segment of the active child (`"summary"`, `"timeline"`, ...).
- Choosing a tab pushes `{base}/{value}`, keeping the query string. The `default` tab writes the bare `base`, so `/orders/1003` stands for `summary` (together with `default_child="summary"`).
- Back, forward and links update the tab, because the segment is read from the URL on every change.
- `base=` replaces the container's base, for example in a `loading.py` that is not given the container. `prop=` syncs another prop, `history="replace"` writes without a history entry, `keep_query=False` drops the query string.

The tabs and the content are two different things: the tab bar lives in the parent (`page.py`), and the content box is the child route (`summary/`, `timeline/`, `notes/`). The showcase's order detail (`pages/orders/[order_id]/page.py`) does this, and `pages/edge-cases/tabs-segment/` is a minimal case.

## Navigate from a callback

```python
from dash import Input, callback

from dash_router import navigate, url_for


@callback(Input("random-order", "n_clicks"), prevent_initial_call=True)
def open_random_order(n_clicks):
    navigate(url_for("orders/[order_id]", order_id=random.choice(order_ids)))
```

`navigate(url)` accepts a string or a `Url`. It works in any callback, with or without an `Output`. It only sets the `href` of the router's location. The router then renders the destination as a normal navigation: skeletons, streamed parts and the title all arrive as they do for a link.

Navigating from a callback takes one more roundtrip than rendering the destination inside the callback did before: the browser first receives the new URL, then requests the page.

After a form submit:

```python
@callback(
    Output("profile-email", "error"),
    Input("profile-save", "n_clicks"),
    State("profile-name", "value"),
    State("profile-email", "value"),
    prevent_initial_call=True,
)
def save_profile(n_clicks, name, email):
    if "@" not in (email or ""):
        return "Enter a valid email address"
    save(name, email)
    navigate(url_for("settings/saved", name=name or ""))
    return None
```

From a clientside callback, set the location yourself:

```javascript
window.dash_clientside.set_props("dash-router-location", { href: "/orders/1003/timeline" });
```

## `url_for`: build URLs from node ids

### Path parameters

```python
url_for("orders/[order_id]", order_id=1003)                               # "/orders/1003"
url_for("orders/[order_id]/timeline", order_id=1003)                      # "/orders/1003/timeline"
url_for("customers/(inspector)/accounts/[customer_id]", customer_id=3)    # "/customers/accounts/3"
url_for("docs/[__rest]", rest=["fulfilment", "shipping"])                  # "/docs/fulfilment/shipping"
url_for("orders/[order_id]", OrderRef(order_id=1003))                      # from a Pydantic path model
```

### Query strings (with or without path parameters)

Any query parameter declared on the route (including active `(slot)`s and `default_child`) can be passed as a keyword argument or as a Pydantic query model:

```python
# Scalar, Enum, bool, and collection query parameters
url_for("overview", range=Range.D7)
# "/overview?range=7d"

url_for("orders", status=OrderStatus.OPEN, page=2)
# "/orders?status=open&page=2"

url_for("reports", tags=["eu", "us"], include_archived=True)
# "/reports?tags=eu,us&include_archived=true"

# `None` and empty collections are omitted
url_for("orders", status=OrderStatus.OPEN, q=None, tags=[])
# "/orders?status=open"

# Pydantic query model: fields equal to their defaults are omitted
filters = OrderFilters(status=OrderStatus.DELAYED, page=2)
url_for("orders", filters)
# "/orders?status=delayed&page=2"

# Path parameter + query arguments together
url_for("orders/[order_id]", order_id=1003, status=OrderStatus.OPEN, page=2)
# "/orders/1003?status=open&page=2"

# Path parameter + Pydantic query model + keyword overrides (None clears a field)
url_for("orders/[order_id]", filters, order_id=1003)
# "/orders/1003?status=delayed&page=2"

url_for("orders/[order_id]", filters, order_id=1003, page=1)
# "/orders/1003?status=delayed&page=1"

url_for("orders/[order_id]", filters, order_id=1003, page=None)
# "/orders/1003?status=delayed"

# Use directly in Link or navigate()
Link("Order #1003", url_for("orders/[order_id]", filters, order_id=1003))
navigate(url_for("orders", status=OrderStatus.DELAYED, q="berg"))
```

If you also need arbitrary/undeclared query parameters (such as UTM tracking tags), wrap the result with `Url.parse(...)`:

```python
Url.parse(url_for("orders/[order_id]", order_id=1003, status=OrderStatus.OPEN)).set_param("utm_source", "email").to_href()
# "/orders/1003?status=open&utm_source=email"
```

- The first argument is a node id as it appears in `router.tree.nodes` (its folder path under `pages/`).
- Slot segments such as `(inspector)` are skipped, because slots never appear in URLs.
- A missing required path parameter raises `ValueError`. Catch-alls take `rest=` (a list or a single string) and may be empty.
- Query parameters use the same encoding as `UrlParam` (`Enum` -> `.value`, `bool` -> `"true"` / `"false"`, collections -> comma-separated).

### Typed route ids and inputs

When `DashRouter(app, pages_folder=...)` scans a pages folder, it automatically generates PEP 561 partial type stubs at `<project_root>/typings/dash_router-stubs/` (override with `stubs_dir=` or disable with `generate_stubs=False`). `url_for` is overloaded for every route id (`RouteId`) with the route's annotated path parameter types, optional query parameters, and Pydantic models:

```python
url_for("orders/[order_id]", order_id=1003, status=OrderStatus.OPEN)  # OK
url_for("orders/[order_id]", filters, order_id=1003)                  # OK

url_for("nonexistent")                                                # Type error: unknown route id
url_for("orders/[order_id]", order_id="1003")                         # Type error: expected int
url_for("orders/[order_id]", filters)                                 # Type error: missing order_id
url_for("orders", status="open")                                      # Type error: expected OrderStatus
url_for("orders", unknown_param="x")                                  # Type error: undeclared query param
```

Because Pyright, Basedpyright, and Pylance automatically discover `typings/` by default, these mistakes are caught with no extra configuration. Stubs are only rewritten when routes or parameter signatures change, so dev servers with `--reload` update stubs automatically on reload without triggering reload loops (call `router.reload()` for in-process reloads).

## `Url`: edit the current URL

`Url` is an immutable URL with helpers that return a new `Url`:

```python
from dash_router import Url, get_current_url

url = get_current_url()                       # in a callback: the page's URL
url.set_param("status", "delayed")            # add or replace a parameter (None removes it)
url.update_params(status="open", page=None)   # several at once, None removes
url.remove_param("q")
url.clear_query()
url.to("/orders/1003")                        # same query, other path
Url.parse("/orders?status=open").to_href()    # "/orders?status=open"
str(url)                                      # same as to_href()
```

Lists are written comma separated: `Url(pathname="/orders", search={"status": ["open", "closed"]}).to_href()` is `/orders?status=open,closed`.

### Reading the current URL

`get_current_url()` reads the `Referer` of the callback request, so it returns the URL of the page that sent the callback. Without a page Referer it returns `/`, or raises `RuntimeError` with `get_current_url(strict=True)`.

Layouts and endpoints of deferred subtrees (`loading.py` boundaries and generator layouts) run inside a streaming callback; when the SharedWorker stream transport is active, the browser sends the worker script as the Referer, so `get_current_url()` returns `/`. Take the values from the layout's arguments (path variables and query values) instead. In your own callbacks, take the location as a `State`:

```python
@callback(Output("out", "children"), Input("button", "n_clicks"), State(RootContainer.ids.location, "href"))
def show(n_clicks, href):
    ...
```

## Page titles

```python
config = RouteConfig(title="Orders · Northwind Ops")
```

`title` is a string, or a function whose parameters are the route's variables: path variables and query values, converted to their annotated types.

```python
def title(order_id: int) -> str:
    return f"Order #{order_id} · Northwind Ops"


config = RouteConfig(title=title)
```

The title comes with the response of each navigation. The browser sets `document.title` to the title of the deepest node on the main branch (following `children`, not slots) that has one. Nodes without a title inherit their parent's. A function that raises is skipped in the same way. If no node of the new URL has a title, the browser keeps the current one. Pass `update_title=None` to `Dash(...)` to stop Dash from showing "Updating..." during navigations.

## The navigation flow

1. The URL changes: a link, `navigate`, back or forward, typing in the address bar, or a `UrlParam` / `UrlCommit` write.
2. The browser sends one navigation callback with the old and new URL. The server plans the transition, runs the endpoints outside lazy boundaries and returns the patched containers.
3. The response carries the title and every container the transition patches. Lazy boundaries show their `loading.py` skeleton in this response ([Transitions](transitions.md#loading-states-come-from-the-server)). Each boundary then streams its content in on its own.
4. The URL is committed together with the response. A newer navigation replaces the older one, and the older one's streams are dropped ([Superseded navigations](transitions.md#superseded-navigations)).

## History while a navigation is in flight

The browser's history gets the new URL in step 1, before the router has answered. If a second navigation overtakes the first, the first URL would stay in the history as an entry that never rendered.

The history guard prevents that. While a navigation is in flight, that is, while the committed `href` (the URL the router last rendered) differs from the browser's `pathname + search`, every `history.pushState` becomes a `replaceState`. Only URLs the router has committed keep an entry of their own. Links, `UrlSegment` tabs and `UrlParam` writes all go through it, and it needs no configuration.

Clicking Slow, then Fast before Slow lands, therefore leaves `/slow` out of the history: the history ends with the page you came from and Fast. The showcase's `/edge-cases/history-superseded` checks this in the browser with `Page.getNavigationHistory`.
