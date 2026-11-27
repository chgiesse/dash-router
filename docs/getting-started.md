# Getting started

## Requirements

- Python 3.12
- Dash 4.5 or newer (the router uses `app.backend`, `dash.set_props` and streaming callbacks)
- The Risk Shield patched `dash-renderer` (`packages/dash`) for streaming `loading.py` boundaries and generator layouts, and for cancelling the streams of dropped navigations. Plain navigation works on stock Dash.
- Pydantic 2
- An async server: Quart or FastAPI. The router streams lazy boundaries and runs endpoints in parallel, which sync servers such as Flask cannot do.

In this repository `dash-router` is a uv workspace package (`packages/dash-router`). Add it to a project with `uv add dash-router`, or run `uv sync` at the repository root.

## Wire the router into a Dash app

```python
# app.py
from pathlib import Path

from dash import Dash
from quart import Quart

from dash_router import DashRouter, RootContainer

APP_DIR = Path(__file__).resolve().parent

server = Quart(__name__)
app = Dash(
    __name__,
    server=server,
    use_pages=False,                    # the router replaces Dash Pages
    suppress_callback_exceptions=True,  # route content arrives after the first page load
)

router = DashRouter(app, pages_folder=APP_DIR / "pages")

app.layout = RootContainer()
```

Run it with any ASGI server, for example:

```bash
granian --interface asgi --host 127.0.0.1 --port 8050 app:server
```

What each piece does:

- `DashRouter(app, pages_folder=...)` scans the folder, imports every route module, validates the tree and registers the router's callbacks on `app`. It is also available afterwards as `app.router`.
- `RootContainer()` holds the `dcc.Location` and the stores the router needs, plus the container the whole page is rendered into. Put it in `app.layout` once. You can wrap it in providers, for example `dmc.MantineProvider(RootContainer())`.
- `suppress_callback_exceptions=True` is required: callbacks of a route reference components that are not in the initial layout.

Other servers:

```python
from fastapi import FastAPI
app = Dash(__name__, server=FastAPI(), use_pages=False, suppress_callback_exceptions=True)

# or let Dash create the server
app = Dash(__name__, backend="fastapi", use_pages=False, suppress_callback_exceptions=True)
```

## Your first pages

```text
pages/
├── page.py          the shell around every page
├── home/
│   └── page.py
└── reports/
    ├── page.py
    └── [report_id]/
        └── page.py
```

```python
# pages/page.py
from dash import dcc, html

from dash_router import ChildContainer, RouteConfig

config = RouteConfig(default_child="home", title="My app")


def page(children: ChildContainer, **_):
    return html.Div(
        [
            html.Nav([dcc.Link("Home", href="/home"), " | ", dcc.Link("Reports", href="/reports")]),
            html.Main(children),
        ]
    )
```

Because the root `page` takes `children`, it becomes a persistent shell: it is rendered once, and every navigation patches only its `children` container. `default_child="home"` makes `/` show `home`.

```python
# pages/home/page.py
from dash import html

page = html.H1("Welcome")
```

```python
# pages/reports/page.py
from dash import dcc, html

from dash_router import ChildContainer


def page(children: ChildContainer, **_):
    links = [dcc.Link(f"Report {i}", href=f"/reports/{i}") for i in (1, 2, 3)]
    return html.Div([html.Aside(links), html.Section(children)], style={"display": "flex", "gap": 24})
```

```python
# pages/reports/[report_id]/page.py
from dash import html


def page(report_id: int | None = None, **_):
    if report_id is None:
        return html.P("Select a report.")
    return html.H2(f"Report {report_id}")
```

Try these URLs:

| URL | Rendered nodes |
| --- | --- |
| `/` | `/`, `home` (through `default_child`) |
| `/reports` | `/`, `reports`, `reports/[report_id]` with `report_id=None` |
| `/reports/2` | `/`, `reports`, `reports/[report_id]` with `report_id=2` |
| `/reports/2` -> `/reports/3` | only `reports/[report_id]` |
| `/nope` | the 404 layout |

`/reports` shows the *omitted* state of `[report_id]` (`report_id=None`). You can also put a `default.py` inside `[report_id]/` to render a separate empty state without handling `None` in `page.py` ([routing](routing.md#omitted-parameters)).

Always end layout signatures with `**_` (or `**kwargs`). The router passes everything the node can see (path variables, query values, slots, `data`), and only keeps the arguments a function accepts when it has no `**kwargs`. Adding `**_` keeps layouts working when you add query parameters later.

## Add data, a skeleton and an error boundary

```text
pages/reports/[report_id]/
├── api.py
├── loading.py
├── error.py
└── page.py
```

```python
# api.py
async def endpoint(report_id: int | None = None, **_):
    if report_id is None:
        return None
    return await fetch_report(report_id)
```

```python
# loading.py
from dash import html

loading = html.Div("Loading report…", className="skeleton")
```

```python
# error.py
from dash import html


def error(error: Exception, **_):
    return html.Div(f"Could not load the report: {error}", className="error")
```

```python
# page.py
def page(data: dict | None = None, report_id: int | None = None, **_):
    ...
```

Now `/reports/3` shows the skeleton in the navigation response, one roundtrip after the click. `endpoint` and `page` run in the background, and the result replaces the skeleton when it is ready. If either raises, `error.py` renders in place of this node only. See [Data, loading and errors](data-loading.md).

## Not found page

```python
def not_found(**_):
    return html.Div([html.H1("404"), dcc.Link("Home", href="/")])


router = DashRouter(app, pages_folder=APP_DIR / "pages", not_found_layout=not_found)
```

`not_found_layout` can be a component or a function. Without it the router renders a plain "404 - Page not found" heading.

## Next steps

- [Routes and URLs](routing.md) explains how folders map to URLs.
- [Layouts and containers](layouts.md) explains what a layout receives.
- The Northwind Ops showcase in `examples/showcase` is a complete app to read alongside these docs.
