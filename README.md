# Dash Router

## Introduction

`DashRouter` is a **file-system based routing** replacement for the default Dash `pages module`. Unlike the conventional direct mapping of pages, Dash Router resolves URLs segment-wise through a route tree. This approach allows you to break down your application into modular pieces, with each URL segment corresponding to a part of your layout and folder in your project.
All routes are dynamic by default and have to be set static manually. Static routes utilize the native mapping with path template support like the dash pages module while dynamic routes are stored and executed via route tree. The tree is constructed by two route types:

- **nested routes**: distinct segment inside the layout, URL and application
- **slots**: silent route segment with isolated placement in the layout and folder

This segmentation not only makes your codebase easier to manage but also enhances performance through subrendering, parallel execution, and individualized error and loading handling.

![routing](route_tree.png)
_Resolving a URL example_

![example](render_example.gif)
_layout and render example_

### Note:

`DashRouter` supports both [`Dash`](https://github.com/plotly/dash) and [`Flash`](https://github.com/chgiesse/flash), but the parallel execution paradimes only apply for Flash, due to its async capatilities. That means that the execution of slots and nested routes with Dash will always be in sequence but the subrenedering, error handling etc will be the same.

## Conventions & Features

Note: Each level needs a distinct route into the next layer, that means that 
each level can only have one dynamic route. So a layer can have slots without any path and a nested route 

- `Slots`: Slots are defined by folder names starting and ending with **(_slot_name_)**
- `Nested Routes`: Nested routes are defined by the foldername
- `Layouts`: The router is looking for **page.py** files which must contain either a **DashComponent** or **function** named **layout**
- `Route Config`: Routes can be configure with the **RouteConfig** object which has to be places in the corresponding **page.py** file
- `Path Templates`: Path templates get set via the RouteConfig: **pathtemplate='<customer_id>'** and will be passed as keyword argument to the corresponding layout and all its child segments
- `Static Routes`: Set **is_static=True** in the **RouteConfig** to render the layout as root without any children
- `Error`: If the rendering of a layout failes, an individual error layout is rendered. To add a custome error handler, place an **error.py** next to your page.py file with either a **DashComponent** or **function** named **layout**
- `Loading`: _In upcoming version_
- `App Modules`: Folders without a page.py file can be removed from the url by setting **ignore_empty_folders=True** in the Router object, this can help to structure your application

## Setup

### Example app structure

```
.
├── app/
├── pages/                              -> Root Route
│   ├── sales/                          -> Root of Nested Route
│   │   ├── _components/
│   │   ├── invoices/                   -> Nested Route
│   │   │   ├── (invoice)/              -> Slot with path template
│   │   │   │   ├── items/
│   │   │   │   │   └── page.py
│   │   │   │   ├── positions/
│   │   │   │   │   └── page.py
│   │   │   │   └── page.py
│   │   │   ├── (vendors)/              -> Slot
│   │   │   │   └── page.py
│   │   │   └── page.py
│   │   ├── overview/
│   │   │   └── page.py
│   │   └── analytics/
│   │       └── page.py
│   ├── monitoring/                     -> Static Route
│   │   └── page.py
│   └── analytics/                      -> App Module
│       ├── dashboard_1/
│       │   └── page.py
│       ├── dashboard_2/
│       │   └── page.py
│       └── dashboard_3/
│           └── page.py
└── app.py
```

## Create App

- Instatiate the router - creates the execution tree _(next version will be able to take a manually configured routing tree)_
- Insert the `RootContainer` - this where your content gets displayed

```python
# app.py
from dash_router import Router, RootContainer
from flash import Flash
from dash import html


app = Flash(__name__, pages_folder='pages')
router = Router(app, ignore_empty_folders=True)

app.layout = html.Div([RootContainer()])
```

- **Don't** set `use_pages=True` in Dash or Flash to avoid routing collisions

## Create Basic Page

- create a `page.py` file in your pages directory - this route is automatically treated as ' / '
- define a layout _(layout definitions for Dash must be sync)_

```python
# pages/page.py -> /
from dash import html
from dash_router import RouteConfig


config = RouteConfig(
    title='Home'
)

async def layout(**kwargs):
    return html.H1('Hello Flash')
```

## Create Nested Routes

- Routes and their folders are automatically nested routes
- Nested routes get pass as `ChildContainer` to their parent layout
- Parent layout defines the position of all child segments
- ChildContainer have a special property `props` with the `active` attribute which contains the name of the active children
- Set default child routes with `default_child`
- _upcoming version will have a method to securely create urls in your layout_

```python
# pages/sales/page.py -> /sales
from ._components.tabs import Tabs

from dash_router import ChildContainer
import dash_mantine_components as dmc


config = RouteConfig(default_child="overview")

async def layout(children: ChildContainer, **kwargs):
    return dmc.Stack(
        [
            dmc.Title("Sales", mt=0, pt=0),
            Tabs(active=children.props.active),
            dmc.Divider(),
            dmc.ScrollArea(
                children,
                h="calc(85vh)",
                type="auto",
                offsetScrollbars=True
            )
        ]
    )
```

## Create Slots

- Slots are silent route segments with the behaviour of a normal nested route
- Positions also get managed by their parent layout

**Parent Route**:

```python
# pages/sales/invoices/page.py -> /sales/invoices
from ._components.table import create_invoice_table
from ._api import get_data

from dash_router import SlotContainer
import dash_mantine_components as dmc


async def layout(vendors: SlotContainer, invoice: SlotContainer, **kwargs):

    data = await get_data()

    return dmc.SimpleGrid(
        cols=2,
        children=[
            dmc.Stack(
                [
                    dmc.Title("Top Vendors", order=2),
                    vendors,
                    dmc.Title("Invoice List", order=3),
                    create_invoice_table(data)
                ]
            ),
            dmc.Stack(
                [
                    dmc.Box(invoice, mih=50),
                    dmc.Alert(
                        "This is still the invoices section",
                        title="Invoices section!",
                    )
                ]
            )
        ]
    )
```

- Slots can also be dynamic but either **none, all or one**
- foldernames have to start and end with () to mark a route as slot
- slots are independent fom each and therefor executed in parallel

**Basic Slot**:

```python
# pages/sales/invoices/(vendors)/page.py -> /sales/invoices
from ._components.figures import create_barchart
from ._api import get_data


async def layout(**kwargs):
    data = await get_data()
    return create_barchart(data)
```

## Path Variables

- Path variables can be applied on static and slot routes
- Path templates in dynamic routes have to be slots
- Get defined in the RouteConfig and contain <>
- static routes can have multiple kwargs in a pathtemplate slots only take one kwarg
- _upcoming version will have type conversions and a <...rest> template that takes all remaing segments as arguments_

**Slot with path variable**:

```python
# pages/sales/invoices/(invoice)/page.py -> /sales/invoices/<invoice_id>
from ._components.figures import create_comp_chart
from ._components.tabs import create_invoice_tabs
from ._api import get_data

from dash_router import RouteConfig, ChildContainer


config = RouteConfig(path_template="<invoice_id>", default_child="items")

async def layout(children: ChildNode, invoice_id: int = None, **kwargs):

    if not invoice_id:
        return dmc.Stack(
            [
                get_icon("carbon:select-01", height=60),
                dmc.Title("No invoice selected", order=3),
            ],
            align="center"
        )

    data = await get_data(invoice_id)

    return dmc.Stack(
        [
            dmc.Title("Invoice ID: " + str(invoice_id), order=2),
            dmc.Card(
                [
                    dmc.Title("All sales of vendor", order=3, mb="md"),
                    create_comp_chart(data),
                ]
            ),
            create_invoice_tabs(children.props.active, invoice_id),
            dmc.Card(children)
        ]
    )
```

**Path template in static route**:

```python
# pages/monitoring/page.py -> /monitoring/<cid>
import dash_mantine_components as dmc
from router import RouteConfig


config = RouteConfig(path_template="<cid>", is_static=True)

async def layout(cid: str, **kwargs):
    return dmc.Title(f"Monitoring {cid}")
```

```python
# pages/monitoring/page.py -> /monitoring/<cid>/unit/<other_id>
import dash_mantine_components as dmc
from router import RouteConfig


config = RouteConfig(path_template="<cid>/unit/<other_id>", is_static=True)

async def layout(cid: str, other_id: str, **kwargs):
    return dmc.Title(f"Monitoring {cid} {other_id}")
```

## Error Layouts

- Add `error.py` file to your route folder with DashComponent or function named layout for custom error handling
- Layout receives the exception as well as the path variables and search params the layout used
- A basic red card with the error message gets displayed by default

```python
import dash_mantine_components as dmc


def layout(e: Exception, *args, **kwargs):
    return dmc.Alert(
        str(e),
        title="Error occured",
        color="red",
        variant="light"
    )
```
