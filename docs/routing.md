# Routes and URLs

The router builds a tree of route nodes from your `pages/` folder when the app starts. Each URL is matched against that tree from the top down.

## Folders become URL segments

```text
pages/
├── page.py                    /            (root)
├── orders/
│   ├── page.py                /orders
│   └── [order_id]/
│       ├── page.py            /orders/1003
│       ├── default.py         /orders      (when [order_id] is omitted)
│       ├── summary/
│       │   └── page.py        /orders/1003 (through default_child="summary")
│       └── timeline/
│           └── page.py        /orders/1003/timeline
└── order_history/
    └── page.py                /order-history
```

- A folder with a `page.py` is a route node. Its **node id** is its path relative to `pages/`: `orders`, `orders/[order_id]`, `orders/[order_id]/timeline`.
- Underscores and spaces in folder names become dashes in the URL (`order_history` -> `/order-history`).
- Folders that start with `_` or `.` are skipped, so `_components/` or `__pycache__/` never become routes.
- A route file that renders (`page.py`, `loading.py`, `error.py`, `default.py`) must define its role function (`page`, `loading`, `error`, `default`) or `layout` (see [Naming](#naming)). Otherwise the router raises `RouteLayoutMissingError` at startup. An import error in any route file raises `RouteModuleImportError` with the file name.

## Naming

Each route file defines a function or component named after the file:

| File | Name | Fallback |
| --- | --- | --- |
| `page.py` | `page` | `layout` |
| `loading.py` | `loading` | `layout` |
| `error.py` | `error` (receives the exception as its first argument: `def error(error: Exception, **_)`) | `layout` |
| `default.py` | `default` | `layout` |
| `api.py` | `endpoint` | — |

`layout` is still accepted in every file as a fallback, so existing route files keep working. Defining both the role name and `layout` in the same file raises `RouteConfigConflictError`: keep one of them. Any existing route file that defines neither raises `RouteLayoutMissingError`.

Trees built with `RouteTree.from_spec` are not affected: their keys (`layout`, `default`, `loading`, `error`, `endpoint`) stay the same.

## Nested routes and `children`

A node renders its child route inside its own page. The child arrives as the `children` argument, a `ChildContainer`:

```python
# pages/orders/page.py
from dash import html

from dash_router import ChildContainer


def page(children: ChildContainer, **_):
    return html.Div([html.H1("Orders"), children])
```

When you navigate between two children (`/orders/1003` -> `/orders/1004`), the `orders` page is not rendered again. The router replaces only what is inside `children`. See [Layouts and containers](layouts.md) for the rules.

## The root: shell or standalone page

`pages/page.py` plays one of two roles:

- **Persistent shell** (the usual case): its `page` function takes `children` or the node has slots. Every other route renders inside it, and it is mounted once per page load.
- **Standalone index page**: its `page` function takes neither. Then `/` is a page of its own, and top-level routes such as `/orders` render directly into the page, without a shell.

## When the URL stops at a parent

What `/orders` shows depends on `orders/` and its children:

| Setup | `/orders` renders |
| --- | --- |
| `default_child="summary"` in `config` | `orders/page.py` with `orders/summary/page.py` inside its `children` (the address bar keeps showing `/orders`). |
| `[order_id]/default.py` | `orders/page.py` with `[order_id]/default.py` (`mode="default"`) inside `children`. |
| `[order_id]/page.py` (no `default.py`) | `orders/page.py` with `[order_id]/page.py` in its *omitted* state (`order_id=None`). |
| Literal children only, no `default_child` | `orders/page.py` with an empty `children` container. |

`default_child` must name a literal child folder; the router checks this at startup and raises `RouteTreeValidationError` otherwise. The router does not warn at runtime when the parent has no default.

## Path parameters: `[param]`

A folder named `[name]` matches any single URL segment and passes it to the node as `name`:

```python
# pages/orders/[order_id]/page.py
def page(order_id: int, **_):
    ...
```

- The value is coerced from the annotation when the function is called: `int`, `float`, `bool`, `str`, an `Enum`, a `Literal[...]`, or any of these with `| None`. Without an annotation you get the raw string.
- Dashes in the folder name become underscores in the argument: `[order-id]` -> `order_id`.
- Child nodes, slots and their endpoints see the path variables of every ancestor, so `pages/orders/[order_id]/timeline/api.py` can take `order_id: int`.
- A node can have only one bare `[param]` (or `[__rest]`) child. A second one raises `ValueError` at startup.

### Omitted parameters

When the URL stops at the parent (`/orders`) and the parent has no `default_child`:

- If `[order_id]` defines `default.py`, `[order_id]` renders in `default` mode (`default.py`) and `[order_id]/page.py`, `api.py` and `loading.py` are skipped. The showcase uses this in `pages/orders/[order_id]/default.py`.
- Otherwise, `[order_id]/page.py` still renders, with `order_id=None` (`omitted=True`). Its `api.py` and `loading.py` are skipped (`data` is `None`), and none of its children render. Give the parameter a default (`order_id: int | None = None`) so the function accepts the missing value.

### Static prefixes: `accounts/[customer_id]`

A folder without a `page.py` adds its name to the next route below it. Use this to put a fixed segment in front of a parameter:

```text
pages/customers/
├── page.py
├── directory/page.py
└── accounts/              no page.py
    └── [customer_id]/
        └── page.py        node id: customers/accounts/[customer_id], URL: /customers/accounts/3
```

The same works for plain routes: `pages/admin/users/page.py` without `pages/admin/page.py` creates one node matched by `/admin/users`.

Pass `DashRouter(..., ignore_empty_folders=True)` to make such folders purely organisational instead: they then add nothing to the URL.

### Matching order

For the remaining URL segments, a node tries its children in this order:

1. Literal child routes, longest prefix first (`reports/annual` before `reports`).
2. Parameters behind a static prefix (`accounts/[customer_id]`).
3. The bare `[param]` or `[__rest]` child.

So `/customers/directory` matches `directory` even though `[customer_id]` would also accept the segment.

## Catch-all routes: `[__rest]`

A folder named `[__rest]` (or `[--rest]`) matches every remaining segment, at any depth, and passes them as `rest: list[str]`:

```python
# pages/docs/[__rest]/page.py
def page(rest: list[str], **_):
    article = find_article(rest)  # /docs/fulfilment/shipping -> ["fulfilment", "shipping"]
    ...
```

- `/docs` itself matches with `rest=[]`. If the folder has a `default.py`, that renders instead.
- A catch-all must be a leaf of its branch. It may have slots but no child routes (`RouteTreeValidationError` otherwise).
- Build links with `url_for("docs/[__rest]", rest=["fulfilment", "shipping"])`.

## Standalone pages: `is_static=True`

```python
# pages/status/page.py
from dash_router import RouteConfig

config = RouteConfig(is_static=True, title="Status wall")


def page(**_):
    ...
```

A static route renders on its own, without the root shell, as if the root were a standalone page. Use it for login screens, wall displays or print views.

- Static routes are matched before any other route.
- They cannot have child routes or slots (`RouteTreeValidationError`).
- Moving between a static route and a normal route re-renders the whole page.

## Not found

A URL is "not found" when no branch matches all of its segments. A route slot that does not match the URL does not cause a 404: it shows its `default.py`, or renders empty (see [Slots and parallel routes](parallel-routes.md#when-a-slot-has-no-match)). The router then renders `not_found_layout` (a component or a function) in place of the whole page:

```python
router = DashRouter(app, pages_folder="pages", not_found_layout=not_found)
```

## Configuring a node with `RouteConfig`

`page.py` can define `config = RouteConfig(...)`. The fields that change routing behaviour:

| Field | Effect |
| --- | --- |
| `default_child` | Child folder rendered when the URL stops at this node. |
| `is_static` | Render this route without the shell. |
| `title` | Document title while this node is the deepest titled node of the main branch ([details](navigation.md#page-titles)). |
| `default`, `loading`, `error` | Inline alternatives to `default.py`, `loading.py` and `error.py`. Defining both the field and the file raises `RouteConfigConflictError`. |

Every field is stored on the node as `node.config.<field>`. `description`, `name`, `order`, `image`, `image_url`, `redirect_from` and `meta` are for your own use, for example to build navigation menus from `router.tree.nodes`: `router.tree.nodes["orders"].config.order`. The router itself does not act on them.

## Seeing the tree

`router.tree.nodes` maps every node id to its `RouteNode`. `router.match(url)` returns the matched tree for a URL (or `None`), and `router.plan(old_url, new_url)` returns what a transition would render. [Testing routes](testing.md) builds on these.
