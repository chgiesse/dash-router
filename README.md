# Dash Router (`dash_router`)

File-system and spec-driven nested & parallel router for **Dash 4.5+** on an async backend (`Quart`, `FastAPI`), using Dash's native backend wrapper (`app.backend`), `dash.set_props`, and streaming generator callbacks.

## Highlights

- **Pure `(old_url, new_url)` Tree Diffing**: Deterministic route resolution and container patching with zero fragile client loading-state stores. Unified handling of path, query-string, and combined transitions.
- **True Parallel Routes in `(slots)`**: Each `(slot)` receives its own forked immutable URL cursor and scoped `path_vars` (zero sibling leakage). Slots can define their own nested child routes, `[param]` templates, and `default.py` fallbacks (with soft-navigation retention when unmatched).
- **Skeletons in the First Frame + Single-Stream Lazy Layouts**: Every URL change runs one streaming server callback. `loading.py` skeletons arrive in its first frame, while `api.py` endpoints and lazy subtrees start immediately and stream over that same callback.
- **First-Class `(old_url, new_url) -> expected segments` Test Framework**: Test complex routing trees in milliseconds via `RouteTester.from_spec(...)` or `RouteTester.from_folder(...)` without starting a server or browser.

## Documentation

The full documentation is in [`docs/`](docs/index.md):

1. [Getting started](docs/getting-started.md)
2. [Routes and URLs](docs/routing.md)
3. [Layouts and containers](docs/layouts.md)
4. [Slots and parallel routes](docs/parallel-routes.md)
5. [Data, loading and errors](docs/data-loading.md)
6. [Query parameters](docs/query-params.md)
7. [Navigation](docs/navigation.md)
8. [Transitions and streaming](docs/transitions.md)
9. [Testing routes](docs/testing.md)
10. [API reference](docs/api-reference.md)
11. [Troubleshooting](docs/troubleshooting.md)

The same pages can be browsed inside the Northwind Ops showcase (`examples/showcase`, run it and open `/documentation`), next to live demos of each feature.

## Quick Start

```python
from dash import Dash, html
from quart import Quart
from dash_router import DashRouter, RootContainer

server = Quart(__name__)
app = Dash(__name__, server=server, pages_folder="pages", use_pages=False)
router = DashRouter(app, pages_folder="pages")

app.layout = html.Div([RootContainer()])
```

## Testing Route Transitions

```python
from dash_router.testing import RouteTester

tester = RouteTester.from_spec({
    "tickets": {
        "[ticket_id]": {
            "(detail)": {"(summary)": {}},
            "(activity)": {"inputs": ["filter"], "(comments)": {}},
        }
    }
})

# Initial render vs incremental transitions:
tester.assert_routes(
    old="/tickets/1001",
    new="/tickets/1001?filter=unread",
    expected=[
        "tickets/[ticket_id]/(activity)",
        "tickets/[ticket_id]/(activity)/(comments)",
    ],
)
```
