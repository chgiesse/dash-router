# dash_router documentation

`dash_router` is a file-system router for Dash 4.5+. You describe your app as a folder tree: each folder is a URL segment, and each `page.py` renders that segment. The router turns a URL into a tree of route nodes. On every navigation it re-renders only the nodes whose inputs changed, and patches them into the page in place.

It is built on Dash's own backend wrapper (`app.backend`) and runs on Quart or FastAPI. Data loads in parallel and the page streams in as each part becomes ready.

## What you get

| Feature | In short | Page |
| --- | --- | --- |
| Nested routes | Folders nest URL segments; a parent layout wraps its child through a `children` container. | [Routes and URLs](routing.md) |
| Persistent layouts | A parent stays mounted while you move between its children. Only the part that changed is rendered. | [Layouts and containers](layouts.md) |
| Path parameters | `[order_id]` folders capture a segment and coerce it to the annotated type. | [Routes and URLs](routing.md#path-parameters-param) |
| Catch-all routes | `[__rest]` captures any number of segments as a list. | [Routes and URLs](routing.md#catch-all-routes-__rest) |
| Parallel slots | `(name)` folders render next to each other in the same layout. They can also match the URL on their own. | [Slots and parallel routes](parallel-routes.md) |
| Data loading | `api.py` endpoints run in parallel before the layout renders and pass their result as `data`. | [Data, loading and errors](data-loading.md) |
| Skeletons and streaming | A `loading.py` skeleton arrives with the navigation. Its content streams in as soon as it is ready. | [Data, loading and errors](data-loading.md#loadingpy-skeletons-and-lazy-boundaries) |
| Error boundaries | An `error.py` replaces only the failing part of the page. | [Data, loading and errors](data-loading.md#errorpy-error-boundaries) |
| Typed query parameters | Layout arguments read the query string, with type coercion, Enums and Pydantic models. | [Query parameters](query-params.md) |
| Fine-grained updates | A query change re-renders only the nodes that declare that parameter. | [Query parameters](query-params.md#subscriptions-who-re-renders) |
| Navigation helpers | `Link`, `navigate`, `url_for` and `Url`. `Link` navigates in-page and marks the active link. | [Navigation](navigation.md) |
| Query state without callbacks | `UrlParam` and `UrlCommit` sync a control with a query parameter, in the browser. | [Query parameters](query-params.md#urlparam-and-urlcommit) |
| Page titles | `title` in `RouteConfig`, set from the server together with the navigation. | [Navigation](navigation.md#page-titles) |
| Route tests | Test `(old_url, new_url) -> rendered segments` without a server or browser. | [Testing routes](testing.md) |

## A first look

```text
pages/
├── page.py                 root shell (header, sidebar), renders `children`
├── overview/
│   ├── page.py             places the two slots below
│   ├── (kpis)/             a slot with its own data and skeleton
│   │   ├── api.py
│   │   ├── loading.py
│   │   └── page.py
│   └── (revenue)/
│       ├── api.py
│       └── page.py
└── orders/
    ├── page.py             /orders: the list and the children box
    └── [order_id]/         /orders/1003 -> order_id=1003
        ├── default.py      /orders: "pick an order" when [order_id] is omitted
        ├── page.py         header + tabs, renders at once (default_child="summary")
        └── summary/
            ├── api.py      loads the order
            └── page.py     /orders/1003: the summary, with data
```

```python
# pages/orders/[order_id]/page.py
from dash import html

from dash_router import ChildContainer, RouteConfig

config = RouteConfig(default_child="summary")


def page(children: ChildContainer, order_id: int, **_):
    return html.Div([html.H2(f"Order #{order_id}"), children])
```

```python
# pages/orders/[order_id]/summary/api.py
async def endpoint(order_id: int, **_):
    return await load_order(order_id)
```

```python
# pages/orders/[order_id]/summary/page.py
from dash import html


def page(data: dict, **_):
    return html.P(f"Status: {data['status']}")
```

The header of `[order_id]/page.py` renders at once. The summary waits for `summary/api.py` behind `summary/loading.py`, if it has one. Going from `/orders/1003` to `/orders/1004` renders only `[order_id]`, header included, because its path variable changed. The root shell and the `orders` layout stay mounted.

## Special files

| File or folder | Role |
| --- | --- |
| `page.py` | Defines `page` (a function or a component) and optionally `config = RouteConfig(...)`. A folder with a `page.py` is a route node. |
| `api.py` | Defines `endpoint(...)`. Its return value is passed to the page as `data`. |
| `loading.py` | Defines `loading`, shown while the node's data and page are being prepared. |
| `error.py` | Defines `error(error, ...)`, rendered when the node's `endpoint` or `page` raises. |
| `default.py` | Defines `default`, rendered when a slot or parameter has nothing to show for the current URL. |
| `callbacks.py` / `callback.py` | Imported automatically when the tree is built, so the callbacks of a route can live next to it. |
| `(name)/` | A slot: rendered in parallel and passed to the parent layout as the `name` argument. |
| `[name]/` | A path parameter: captures one URL segment as `name`. |
| `[__rest]/` | A catch-all: captures all remaining segments as `rest: list[str]`. |
| `_name/`, `.name/` | Ignored, so you can keep helpers next to your routes. |

Any other `.py` file in a route folder (for example `models.py`) is not a route, but it can be imported. Route folders become importable packages, so `from ..models import OrderFilters` works even inside `(slot)` and `[param]` folders.

## Words used in these docs

- **Node**: one route folder (with `page.py`, or a slot with only `default.py` / sub-routes). Its id is its path relative to `pages/`, for example `orders/[order_id]` or `overview/(kpis)`.
- **Container**: the `html.Div` the router passes into a layout (`children`, or one per slot). The router patches containers in place on later navigations.
- **Transition**: one navigation from an old URL to a new URL. The router compares what both URLs match and patches only the containers whose content changed.
- **Frame**: one batch of container updates sent to the browser. A navigation sends its response (the patched containers) at once, and each lazy boundary or generator layout then sends its own frames as it finishes.

## Pages

1. [Getting started](getting-started.md): install, wire the router into a Dash app, write the first pages.
2. [Routes and URLs](routing.md): nested routes, `default_child`, path parameters, catch-alls, standalone pages, 404.
3. [Layouts and containers](layouts.md): what a layout receives and the rules for rendering containers.
4. [Slots and parallel routes](parallel-routes.md): passive slots, slots with their own routes, `default.py` and empty slots.
5. [Data, loading and errors](data-loading.md): `api.py`, `loading.py`, streaming and `error.py`.
6. [Query parameters](query-params.md): typed parameters, Pydantic models, subscriptions, extra routing inputs.
7. [Navigation](navigation.md): links, `Link`, `navigate`, `url_for`, `Url`, page titles.
8. [Transitions and streaming](transitions.md): what happens during a navigation, and when loading states appear.
9. [Testing routes](testing.md): `RouteTester` and inline route specs.
10. [API reference](api-reference.md): every public class and function.
11. [Troubleshooting](troubleshooting.md): common mistakes and how to spot them.

The Northwind Ops showcase (`examples/showcase`) is a working app that uses every feature on this list. Each page of these docs links to the part of the app that demonstrates it.
