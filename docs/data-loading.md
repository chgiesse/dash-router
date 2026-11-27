# Data, loading and errors

Three files next to a `page.py` control how a node gets its data, what it shows while waiting, and what it shows when something fails.

```text
pages/overview/(activity)/
├── api.py       fetch the data
├── loading.py   skeleton while fetching
├── error.py     shown instead of the node if fetching or rendering fails
└── page.py      render the data
```

## `api.py`: endpoints

```python
# pages/orders/[order_id]/summary/api.py
async def endpoint(order_id: int, **_):
    order = await orders_service.get(order_id)
    return {"order": order, "customer": await customers_service.get(order.customer_id)}
```

```python
# pages/orders/[order_id]/summary/page.py
def page(data: dict, **_):
    ...
```

- `endpoint` can be `async def` or a plain function. It receives the same arguments as the page: path variables, query values and Pydantic query models. It does not receive containers or `data`.
- Its return value is passed to `page` as `data`. Return whatever the page needs: dicts, dataclasses or Pydantic models. The value stays on the server and is never serialized.
- The endpoints of **all nodes rendered by a transition run at the same time**. A page with four slots that each wait 0.5 s takes about 0.5 s, not 2 s.
- Endpoints only run for nodes that actually render. They are skipped for nodes that the transition leaves untouched, for `default.py` renders, for omitted parameters and for empty slots.
- The endpoints below a `loading.py` boundary, or inside a generator layout, run in that boundary's own stream, not before the navigation response ([Transitions](transitions.md#two-responses-per-navigation)).
- The query parameters an endpoint declares are subscriptions of the node, exactly like page arguments ([Query parameters](query-params.md)).

Keep `page` fast and pure, and do the I/O in `endpoint`. The router can then start every endpoint up front and render each page as soon as its data is ready.

## `loading.py`: skeletons and lazy boundaries

```python
# pages/overview/(kpis)/loading.py
import dash_mantine_components as dmc

loading = dmc.SimpleGrid([dmc.Skeleton(height=78) for _ in range(4)], cols=4)
```

A node with a `loading.py` is a **lazy boundary**. A generator layout (one that uses `yield`, or an `async def` generator) is also deferred, even without a `loading.py`. When a navigation renders one:

1. The navigation response contains the skeleton in place of the node. Without a `loading.py`, the place is empty.
2. The node's endpoint, its layout and everything below it run in the node's own stream.
3. When they finish, the result replaces the skeleton. A generator layout keeps sending its frames until it returns.

Each boundary streams on its own, in the order the boundaries finish. In the showcase overview, KPIs arrive at about 1.5 s, Revenue at 2.5 s and Activity at 3.5 s.

**Skeletons arrive with the navigation.** The skeleton is part of the navigation response, so it shows after one roundtrip: after the click or the page load, not before it. Each boundary's skeleton is rendered by the server, so it can take arguments (for example `def loading(order_id: int)`).

**Cached data does not skip the skeleton.** Every boundary shows its skeleton first, even when its data is already available, and its content replaces the skeleton when its stream sends it.

**Without `loading.py`, an endpoint delays the response.** Endpoints outside any boundary must finish before the navigation response is sent, because their nodes have nothing to show yet. Rule of thumb: every `api.py` that can be slow gets a `loading.py`.

**Nested boundaries.** A boundary inside another boundary gets its own skeleton inside the outer content and streams on its own. In the showcase, a fresh load of `/orders/1003/timeline` first shows `[order_id]` and then, when it arrives, its timeline, which may still show `timeline/loading.py`. Switching from the Summary tab to Timeline renders only `timeline`, so `timeline/loading.py` shows and `timeline/api.py` streams in on its own.

## `error.py`: error boundaries

```python
# pages/overview/(activity)/error.py
import dash_mantine_components as dmc


def error(error: Exception, **_):
    return dmc.Alert(f"{type(error).__name__}: {error}", title="Recent activity is unavailable", color="red")
```

- The error layout receives the exception as its first argument, plus the node's path variables and query values.
- It renders **in place of this node only** when the node's `endpoint`, `page` or skeleton raises, including when a boundary's own stream fails. Siblings, slots and parents render normally.
- Every node is a boundary. Without an `error.py`, a failing node shows a small default banner ("Error loading route: ...", CSS class `dash-router-error-banner`) instead of breaking the page.
- If the error layout itself raises, the default banner is shown.
- Errors in child nodes are caught by the child's own boundary, not by the parent's `error.py`.

A failed node re-renders on the next transition that touches it, so a link back to the same page with different parameters (or a "Retry" link) is enough to recover.

## Inline alternatives

Instead of separate files you can set the same layouts on the node's config:

```python
config = RouteConfig(loading=skeleton, error=error_layout, default=fallback)
```

Defining both the field and the file raises `RouteConfigConflictError` at startup.

## Choosing the boundaries

| Situation | Do this |
| --- | --- |
| A panel that loads slowly | Put it in its own slot with `api.py` + `loading.py`. |
| Several panels on one page | One slot per panel: they load in parallel, stream separately and fail separately. |
| A detail page with tabs | Put the header and tabs in `[id]/page.py` with `default_child="summary"`, and put `api.py` + `loading.py` inside `summary/`. The header stays visible while the content loads, and tabs without `api.py` (like `notes/`) render at once. |
| Data that does not change | No `api.py`. The node has nothing to wait for, so it renders in the navigation response. |
| Something that can fail | `error.py` in the smallest node that contains it. |
| Filters, search or pagination for a list that has a `loading.py` | Render the controls in the parent, outside the boundary. Otherwise the skeleton replaces them every time the list reloads. Let the parent read the initial values from `**kwargs` (no subscription, so it is not re-rendered) and keep the controls in sync with the URL on the client. The showcase's order list (`pages/orders/page.py`) does this. |
