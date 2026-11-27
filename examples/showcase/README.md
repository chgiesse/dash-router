# Northwind Ops: a showcase for `dash_router`

Northwind Ops is a small e-commerce back office (overview, orders, customers, a knowledge base, a status wall and settings) built to exercise every feature of the file-system router in `dash_router`. Each card shows a `rendered HH:MM:SS.mmm` badge with the server time of its last render. If the badge does not change after a navigation, that part was not re-rendered. The header has a **View code for this page** button. It opens a drawer with the project's folder structure in a Mantine `Tree`: the files the router executed for the current URL are bold and blue (with `default`/`empty` noted), their folders are expanded, and the page the URL points at is selected. Click any file in the tree to show its code next to it; switching files happens in the browser without a server request.

## Run it

From the repository root:

```bash
cd examples/showcase && granian --interface asgi --host 127.0.0.1 --port 8060 app:server
```

Then open <http://127.0.0.1:8060>.

Tests (route transitions, no server or browser needed), from the repository root:

```bash
pytest examples/showcase/tests -q
```

## Documentation

The full documentation for `dash_router` lives in `docs/` as Markdown. The app renders those files at `/documentation`, with a sidebar of pages. Links between doc pages work inside the app.

## Route tree

```text
pages/
├── page.py                      root shell: children, default_child="overview", AppShell, code drawer
├── overview/
│   ├── page.py                  four passive (slots) side by side
│   ├── models.py                Range enum
│   ├── (kpis)/                  api.py (1.5 s), loading.py skeleton, page.py
│   ├── (revenue)/               api.py (2.5 s initial batch), loading.py (spinner), page.py (1 s live Patch stream)
│   ├── (live)/                  page.py: generator layout streaming LiveFeed via Patch + set_props
│   └── (activity)/              api.py (3.5 s, can fail), loading.py, error.py boundary, page.py
├── orders/
│   ├── page.py                  master/detail layout: listing slot + [order_id] child; filters and pagination
│   ├── models.py                OrderFilters (Pydantic query model), PAGE_SIZE
│   ├── (listing)/page.py        generator pushing OrdersTable skeleton, streaming set_data / append_data
│   └── [order_id]/              int path param; default_child="summary"
│       ├── default.py           shown at /orders when [order_id] is omitted ("No order selected")
│       ├── page.py              header from ORDERS, renders at once; tabs = UrlSegment(default="summary")
│       ├── tabs.py              the order tab bar
│       ├── summary/             api.py (2.0 s), loading.py skeleton, page.py
│       ├── timeline/            api.py (2.5 s), loading.py (its own boundary), page.py
│       └── notes/page.py        no api.py / loading.py: renders at once
├── customers/
│   ├── page.py                  children + (inspector) + (pinned) slots; default_child="directory"
│   ├── directory/page.py
│   ├── segments/page.py
│   ├── insights/page.py         only reachable by a soft navigation under (pinned), see below
│   ├── accounts/[customer_id]/  main branch: api.py, loading.py, page.py
│   ├── (inspector)/             slot; page.py (wrapper with placeholder), default.py (no match fallback)
│   │   ├── default.py
│   │   └── accounts/[customer_id]/   api.py (2.8 s), loading.py, page.py
│   └── (pinned)/                slot with no default.py
│       ├── directory/page.py
│       ├── segments/page.py
│       └── accounts/[customer_id]/page.py
├── docs/
│   ├── page.py                  sidebar tree + one catch-all child
│   └── [__rest]/                catch-all: rest=[...] for any depth
│       ├── page.py
│       └── default.py           renders for /docs itself (zero segments)
├── documentation/
│   ├── page.py                  sidebar with one NavLink per doc page + children
│   └── [topic]/page.py          omitted param renders index; no api.py / loading.py
├── settings/
│   ├── page.py                  default_child="profile"
│   ├── profile/page.py          form; save callback calls navigate()
│   └── saved/page.py            confirmation page, reached by navigate
└── status/page.py               is_static=True: mounted without the shell
```

Special files:

| File | Role |
| --- | --- |
| `page.py` | Renders the node. Its signature receives `children` (child container), slot containers, `data` from `api.py`, path variables and typed query params. |
| `api.py` | `async def endpoint(...)`. Runs in parallel with the other nodes of the same URL and streams its result into `data`. |
| `loading.py` | `loading`: static skeleton sent in the first frame while `api.py` runs. |
| `error.py` | `error(error, ...)`. Replaces only its own node when its `api.py` or the node's own function raises. |
| `default.py` | `default`: rendered when a slot or catch-all has no matching child for the current URL. |
| `models.py` | Plain Python helpers (enums, Pydantic models) imported by sibling files. Not routes. |
| `(name)/` | Parallel slot: a passive container passed to the parent layout as a `SlotContainer` argument. |
| `[name]/` | Path parameter, coerced from its annotation (`int`, `list[str]` for `[__rest]`, ...). |

## Walkthrough

Shared paths below are relative to this folder.

### 1. Persistent shell

- **URL:** `/overview`
- **Do:** click around the sidebar.
- **Watch:** the `shell rendered` badge in the header never changes. The root layout is mounted once and only its `children` container is patched.
- **Files:** `pages/page.py`, `ui.py`

```python
    return dmc.AppShell(
        [
            dmc.AppShellHeader(header),
            dmc.AppShellNavbar(navbar, p="sm"),
            dmc.AppShellMain(children),
            code_drawer(),
        ],
```

### 2. Parallel data + streaming

- **URL:** `/overview`
- **Do:** reload the page.
- **Watch:** skeletons appear in frame 0, then each slot streams in when its own `api.py` finishes (KPIs at 1.5 s, Revenue at 2.5 s, Activity at 3.5 s).
- **Files:** `pages/overview/page.py`, `pages/overview/(kpis)/api.py`, `pages/overview/(kpis)/loading.py`

```python
async def endpoint(**_):
    await simulate_latency(1.5)
    orders = list(ORDERS.values())
    return {
        "orders": len(orders),
        "open": sum(o.status is OrderStatus.OPEN for o in orders),
```

### 3. Query params scoped to a slot

- **URL:** `/overview?range=7d`
- **Do:** switch the revenue range.
- **Watch:** only the Revenue card gets a new badge. KPIs and Activity do not subscribe to `range`.
- **Files:** `pages/overview/page.py`, `pages/overview/models.py`, `pages/overview/(revenue)/api.py`, `pages/overview/(revenue)/loading.py`, `pages/overview/(revenue)/page.py`

```python
async def endpoint(range: Range = Range.D30, **_):
    # Typed query param: `?range=7d` arrives as `Range.D7`. Only this slot subscribes to it.
    await simulate_latency(2.5)
    return revenue_series(range.days)
```

### 4. Error boundaries

- **URL:** `/overview?fail=activity`
- **Do:** open the link.
- **Watch:** Activity raises; its `error.py` renders in place while its siblings stay healthy.
- **Files:** `pages/overview/(activity)/api.py`, `pages/overview/(activity)/error.py`

```python
async def endpoint(fail: str | None = None, **_):
    await simulate_latency(3.5)
    if fail == "activity":
        raise UpstreamError("activity service timed out after 3.5 s")
```

### 5. Master / detail

- **URL:** `/orders`
- **Do:** open Orders without an id, then pick one.
- **Watch:** `orders/page.py` renders at once with the list. `[order_id]/default.py` shows the "No order selected" empty state when `[order_id]` is omitted. Picking an order switches `[order_id]` from `default` to `page` mode and patches only `orders`'s `children` box.
- **Files:** `pages/orders/page.py`, `pages/orders/[order_id]/default.py`, `pages/orders/[order_id]/page.py`

```python
def default():  # pages/orders/[order_id]/default.py
    return dmc.Card(dmc.Stack([dmc.Title("No order selected", order=4), ...]))
```

### 6. Smart query models

- **URL:** `/orders?status=delayed`
- **Do:** filter, then open an order.
- **Watch:** the list keeps its badge when you select an order. It only re-renders when a filter changes, because the detail does not subscribe to the query.
- **Files:** `pages/orders/models.py`, `pages/orders/(listing)/page.py`

```python
    status: OrderStatus = OrderStatus.ALL
    q: str = ""
    page: int = Field(default=1, ge=1)
```

### 7. Nested tabs + lazy boundary

- **URL:** `/orders/1003`
- **Do:** open the Timeline tab.
- **Watch:** the header and tabs render at once. The tabs are a `UrlSegment`: Summary is the bare URL (`default_child="summary"`), Timeline pushes `/orders/1003/timeline`, and back selects Summary again. Summary and Timeline each have their own `loading.py` and `api.py`, while Notes renders at once.
- **Files:** `pages/orders/[order_id]/page.py`, `pages/orders/[order_id]/summary/page.py`, `pages/orders/[order_id]/tabs.py`, `pages/orders/[order_id]/timeline/api.py`, `pages/orders/[order_id]/timeline/loading.py`

```python
tabs = UrlSegment(order_tabs(), children, default="summary")
```

```python
async def endpoint(order_id: int, **_):
    await simulate_latency(2.5)
    return order_timeline(ORDERS[order_id])
```

### 8. Parallel routes

- **URL:** `/customers/accounts/3`
- **Do:** open a few customers, then Segments.
- **Watch:** the `(inspector)` slot matches `accounts/[customer_id]` on its own cursor. On Segments it falls back to its `default.py`, while `(pinned)` has its own `segments` route.
- **Files:** `pages/customers/page.py`, `pages/customers/(inspector)/accounts/[customer_id]/api.py`, `pages/customers/(inspector)/default.py`

```python
async def endpoint(customer_id: int, **_):
    # Runs in parallel with the main branch's api.py for the same URL.
    await simulate_latency(2.8)
    return CUSTOMERS[customer_id]
```

### 9. Soft-nav retention

- **URL:** `/customers/insights`
- **Do:** open a customer first, then Insights.
- **Watch:** `(pinned)` has no `insights` route, so it keeps showing the last pinned customer. Reloading this URL directly returns 404 (see the feature map).
- **Files:** `pages/customers/page.py`, `pages/customers/(pinned)/page.py`, `pages/customers/insights/page.py`

```text
Next to the main child route, two `(slots)` define their *own* routes:

- `(inspector)` matches `accounts/[customer_id]` and falls back to `default.py` elsewhere.
- `(pinned)` matches `accounts/[customer_id]`, `directory` and `segments` but has no
  `default.py`: on `/customers/insights` a soft navigation keeps its current content
  (retention), while a hard load of that URL cannot be resolved.
```

The module docstring of `pages/customers/page.py` is the explanation; it is quoted here as the excerpt.

### 10. Catch-all routes

- **URL:** `/docs/fulfilment/shipping/returns`
- **Do:** browse the knowledge base.
- **Watch:** one page (`[__rest]/page.py`) receives `rest=[...]` for any depth. `/docs` itself renders `[__rest]/default.py`. Unknown paths still match and show an "Article not found" alert.
- **Files:** `pages/docs/[__rest]/page.py`, `pages/docs/[__rest]/default.py`, `pages/docs/page.py`

```python
def page(rest: list[str], **_):
    crumbs, page = resolve_doc(rest)
    breadcrumbs = dmc.Breadcrumbs([link("Docs", "/docs")] + [link(title, href) for title, href in crumbs])
    if page is None:
```

### 11. Standalone route

- **URL:** `/status`
- **Do:** open the wall display.
- **Watch:** the page renders without the shell (no header or sidebar). Going back to `/overview` re-mounts the shell.
- **Files:** `pages/status/page.py`

```python
config = RouteConfig(is_static=True, title="Status wall · Northwind Ops")


def page(**_):
    counts = {s: sum(o.status is s for o in ORDERS.values()) for s in OrderStatus if s is not OrderStatus.ALL}
```

### 12. Navigate from a callback

- **URL:** `/settings`
- **Do:** save the profile form.
- **Watch:** the save callback calls `navigate()`, which only sets the location. The router then renders the confirmation page as a normal navigation, one roundtrip later than rendering it inside the callback would take.
- **Files:** `pages/settings/profile/page.py`, `pages/settings/saved/page.py`, `pages/page.py` (`navigate` and `url_for` in the random-order button)

```python
    target = url_for("settings/saved", name=name or "")
    navigate(target)
```

### 13. Not found

- **URL:** `/does/not/exist`
- **Do:** open an unknown URL.
- **Watch:** the router renders the app's 404 layout, passed as `not_found_layout`.
- **Files:** `app.py`

```python
def not_found(**_: object) -> dmc.Center:
    return dmc.Center(
        dmc.Stack(
            [
                dmc.Title("404 · Nothing here", order=2),
```

```python
router = DashRouter(app, pages_folder=APP_DIR / "pages", not_found_layout=not_found)
```

### 14. Edge cases

- **URL:** `/edge-cases` (a jump nav lists every case; each card says what to expect)
- **Do:** click through the races, streams and fallbacks. The debug panel shows this worker's pid and active generators.
- **Watch:**
  - `/edge-cases/history-superseded`: click Slow, then Fast before Slow lands. The history has no Slow entry (the history guard).
  - `/edge-cases/tabs-segment`: Tab A is the default (`default_child="a"`). Clicking B or C pushes its URL; back and forward select the tab again.
- **Files:** `pages/edge-cases/history-superseded/`, `pages/edge-cases/tabs-segment/`, `edge_helpers.py`

## Feature map

| Feature | Where in the app | Files |
| --- | --- | --- |
| Persistent root shell with `children` | Whole app: header and sidebar; the router patches only `children` | `pages/page.py` |
| Nested routes and `default_child` | `/orders/1003` (`summary`), `/customers` (`directory`), `/settings` (`profile`), `/overview` | `pages/orders/[order_id]/page.py`, `pages/customers/page.py`, `pages/settings/page.py`, `pages/page.py` |
| Omitted `[param]` with `default.py` | `/orders` ("No order selected") | `pages/orders/[order_id]/default.py` |
| `UrlSegment` tabs | Order detail tabs; `/edge-cases/tabs-segment` | `pages/orders/[order_id]/page.py`, `pages/edge-cases/tabs-segment/page.py` |
| History guard | `/edge-cases/history-superseded` | `pages/edge-cases/history-superseded/` |
| `[param]` with typed `int` coercion | `/orders/1003`, `/customers/accounts/3` | `pages/orders/[order_id]/summary/api.py`, `pages/customers/accounts/[customer_id]/page.py` |
| Catch-all `[__rest]` and `default.py` | `/docs/...` (any depth), `/docs` (default) | `pages/docs/[__rest]/page.py`, `pages/docs/[__rest]/default.py` |
| Passive `(slots)` | Overview cards, Orders listing, Customers inspector and pinned panels | `pages/overview/page.py`, `pages/orders/page.py`, `pages/customers/page.py` |
| Parallel slots with independent URL cursors | `/customers/accounts/3`: main branch and `(inspector)` both parse `customer_id` | `pages/customers/page.py`, `pages/customers/(inspector)/accounts/[customer_id]/` |
| Slot `default.py` | `(inspector)` on `/customers/segments` | `pages/customers/(inspector)/default.py` |
| Soft-navigation retention | `(pinned)` on `/customers/insights` keeps its last content | `pages/customers/(pinned)/page.py`, `pages/customers/insights/page.py` |
| Hard load of `/customers/insights` returns 404 | `(pinned)` has no `insights` route and no `default.py`, so a fresh load cannot resolve it | `pages/customers/insights/page.py`, `tests/test_showcase_routes.py` |
| `is_static=True` | `/status` mounted without the shell | `pages/status/page.py` |
| Typed query params (`Enum`) | `?range=7d` on Overview; `Range` enum | `pages/overview/models.py`, `pages/overview/(revenue)/api.py` |
| Pydantic query model | `/orders?status=delayed&q=berg&page=2` parsed into `OrderFilters` | `pages/orders/models.py`, `pages/orders/(listing)/page.py` |
| `api.py` parallel fetching | Every Overview card, every order and customer branch | `pages/overview/*/api.py`, `pages/orders/*/api.py`, `pages/customers/*/api.py` |
| `loading.py` skeletons and streamed lazy boundaries | Sent in frame 0 on Overview; `timeline/loading.py` on order detail | `pages/overview/*/loading.py`, `pages/orders/[order_id]/timeline/loading.py` |
| `error.py` boundary | `/overview?fail=activity` | `pages/overview/(activity)/error.py`, `pages/overview/(activity)/api.py` |
| `url_for`, `navigate` | Random-order button, account links, settings save | `pages/page.py`, `pages/customers/accounts/[customer_id]/page.py`, `pages/settings/profile/page.py` |
| `not_found_layout` | Unknown URLs | `app.py` |
| Generator `page` streaming (`set_props` + `Patch`) | Live feed + Orders table push initial shell in Frame 0 and stream rows via classmethods | `pages/overview/(live)/page.py`, `pages/orders/(listing)/page.py` |
| `RouteTester` tests | Transition tests for each tour step, no server or browser | `tests/test_showcase_routes.py` |

## Gotchas learned building this app

**(a) A layout must always render the containers it receives.** The router patches `children` and slot containers in place on later navigations, without re-rendering the parent. If a layout does not render them, there is nothing to patch. The inspector and pinned slots therefore always render `children`, and show a placeholder through the `.slot-hint` CSS trick in `assets/showcase.css`: the hint is hidden unless the container is empty.

```python
    hint = dmc.Text("Open a customer to inspect their risk profile.", size="sm", c="dimmed", className="slot-hint")
    return dmc.Card(
        [
            dmc.Group([dmc.Text("Inspector", fw=600), feature_tags("(inspector) slot route")], justify="space-between", mb="xs"),
            html.Div([children, hint], className="slot-children"),
```

**(b) A `[param]` inside a slot matches any single segment.** `(inspector)/accounts/[customer_id]` must be written with the static prefix `accounts/`. Without the prefix, a bare `[customer_id]` would also match `segments` and `insights` as customer ids. With the prefix, those URLs fall through to `default.py`.

**(c) Layout parameters are subscriptions.** A slot re-renders only when the query params named in its `page.py` or `api.py` signature change. `range` in `(revenue)` is why Revenue updates on a range change while KPIs and Activity keep their badges. A `**kwargs` catch-all subscribes to nothing, so do not rely on it for reactivity.

**(d) Do not name a slot like a query param.** A slot argument shadows the query value of the same name in `**kwargs`. Choose slot names that differ from the query keys a layout reads (here, `range`, `status`, `q`, `page`, `fail`, `name`).

**(e) Keep controls that change the query outside the slot boundary.** While `(listing)` re-renders for a new query, its Frame 0 replaces everything inside the slot. If the order list rendered its own status filter and pagination, they would re-mount on every filter change. They live in `pages/orders/page.py` instead, which does not subscribe to the filters (it reads its initial values from `**query`) and so is never re-rendered by them. Each control is wrapped in `dmc.UrlParam(..., twoWay=True)` to sync with the query string directly with no clientside callbacks; `(listing)/page.py` is a generator `page` that pushes `OrdersTable` with skeleton rows in Frame 0, disables pagination without clearing the count, streams rows via `OrdersTable.set_data` / `OrdersTable.append_data`, and updates the pagination and count via `dash.set_props` once finished. The row highlight is a clientside callback on the table body, so it also runs after each render of the listing: a layout runs inside a streaming callback, where `get_current_url()` cannot see the page URL.

## Files

- `app.py`: Quart server, Dash app, `DashRouter` setup, `not_found_layout`, root layout.
- `data.py`: in-memory customers, orders and docs; `simulate_latency` for the artificial delays.
- `ui.py`: shared building blocks (`rendered_badge`, `section`, `loading_card`, `link`).
- `code_viewer.py`: the code drawer (`dmc.Tree` of the project + code panel) shown by the header button.
- `docs_site.py`: the doc page list (`DOC_PAGES`), `load_doc`, and the link rewriting for `/documentation`.
- `assets/showcase.css`: the `.slot-hint` rule and the `.docs-markdown` styles.
- `assets/docs_links.js`: soft navigation for links inside the rendered Markdown.
- `tests/test_showcase_routes.py`: one `RouteTester` test per feature area.
