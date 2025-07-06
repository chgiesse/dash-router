# Dash Router

## Introduction

`DashRouter` is a **file-system based** and **data centric** routing replacement for the default Dash `pages module`. Unlike the conventional direct mapping of pages, Dash Router resolves URLs segment-wise through a route tree. This approach allows you to break down your application into modular pieces, with each URL segment corresponding to a part of your layout and folder in your project.
All routes are dynamic by default and have to be set static manually. Static routes utilize the native mapping with path template support like the dash pages module while dynamic routes are stored and executed via route tree. The tree is constructed by two route types:

- **nested routes**: distinct segment inside the layout, URL and application
- **slots**: silent route segment with isolated placement in the layout and folder
- **path templates**: dynamic route segments defined by `[folder_name]` that capture URL parameters

This segmentation not only makes your codebase easier to manage but also enhances performance through subrendering, parallel execution, and individualized error and loading handling. 
In addition to that, Dash Router lets you encapsulate your data from the layout. This enables the router to collect all data functions / api endpoints in a linear structure and execute all in one. 

![routing](animated_router.gif)
_Resolving a URL example_

<!-- ![example](render_example.gif)
_layout and render example_ -->

### Note:

`DashRouter` supports both [`Dash`](https://github.com/plotly/dash) and [`Flash`](https://github.com/chgiesse/flash), but the parallel execution paradimes only apply for Flash, due to its async capatilities. That means that the execution of slots and nested routes with Dash will always be in sequence but the subrenedering, error handling etc will be the same.

## Conventions & Features

Note: Each level needs a distinct route into the next layer, that means that 
each level can only have one dynamic route. So a layer can have slots without any path and a nested route 

- `Slots`: Slots are defined by folder names starting and ending with **(_slot_name_)**. They are silent route segments that don't appear in the URL but provide isolated content areas within a layout. Perfect for sidebars, headers, or modular dashboard components that can be positioned independently by their parent layout. **Advantages**: Parallel execution (Flash), independent error handling, reusable components, and isolated state management.

- `Nested Routes`: Nested routes are defined by the foldername and create hierarchical URL structures. Each nested route receives its children as a `ChildContainer` and can position them anywhere in its layout. This enables complex multi-level navigation with shared layouts and breadcrumbs. **Advantages**: Shared layouts reduce code duplication, automatic breadcrumb generation, consistent navigation patterns, and modular component architecture.

- `Path Templates`: Defined by **[path_template_name]** while the name also defines the name of the variable. These create dynamic routes that capture URL segments as function parameters. For example, `[user_id]` creates a route that captures the user ID from the URL and passes it to your layout function as `user_id`. **Advantages**: Type-safe URL parameters, automatic parameter extraction, SEO-friendly URLs, and bookmarkable dynamic content.

- `Smart Query Params`: URL query parameters automatically update the UI based on layout function input params. The router handles type conversion and validation, supporting both basic Python types and Pydantic models. The router automatically selects and re-renders all related layouts that have input parameters matching the query string keys. Currently supports one-level Pydantic models, with model fields used for intelligent matching. Type checking is an upcoming feature. This enables bookmarkable filtered views and shareable URLs with state. **Advantages**: Automatic type validation, shareable filtered states, browser back/forward support, intelligent layout selection, and clean separation of UI state from application state.

- `Layouts`: The router looks for **page.py** files which must contain either a **DashComponent** or **function** named **layout**. These define the visual structure and content for each route. Layouts receive data, path variables, and child components as parameters. **Advantages**: Consistent file structure, automatic component discovery, clear separation of concerns, and predictable routing behavior.

- `Data Injection`: The router automatically collects and executes data functions before rendering layouts, injecting the data into layout functions as the `data` argument. This separates data fetching from presentation logic and enables parallel data loading for better performance. **Advantages**: Parallel data fetching, automatic error boundaries, clean component logic, and optimized loading strategies.

- `Route Config`: Routes can be configured with the **RouteConfig** object which must be placed in the corresponding **page.py** file. This controls route behavior like static rendering, default children, titles, and other metadata. **Advantages**: Centralized route configuration, metadata management, SEO optimization, and flexible routing strategies.

- `Static Routes`: Set **is_static=True** in the **RouteConfig** to render the layout as root without any children. These routes don't participate in the nested routing system and are useful for standalone pages like about pages, login forms, or documentation. **Advantages**: Simplified routing for standalone pages, better performance for simple routes, clean URL structure, and reduced complexity for basic pages.

- `Error Handling`: If the rendering of a layout fails, an individual error layout is rendered. Place an **error.py** file next to your page.py with either a **DashComponent** or **function** named **layout** for custom error handling. The error layout receives the exception and all route parameters. **Advantages**: Granular error control, user-friendly error messages, graceful degradation, and detailed error context for debugging.

- `Loading States`: Place a **loading.py** file with a layout function or component in your route folder and this layout gets loaded first. This only applies when you also have a related data function, providing automatic loading states during data fetching. **Advantages**: Automatic loading UX, reduced perceived loading time, better user experience, and consistent loading patterns across the application.

- `App Modules`: Folders without a page.py file can be removed from the URL by setting **ignore_empty_folders=True** in the Router object. This helps structure your application by allowing organizational folders that don't create routes, keeping URLs clean and organized. **Advantages**: Clean URL structure, flexible code organization, logical file grouping, and separation of routing from code organization.

## Upcoming Features

Dash Router is actively developed with several powerful features planned for future releases:

### Redirect Functions
Programmatic navigation with automatic URL updates and state management.

```python
from dash_router import redirect

async def layout(**kwargs):
    if not user_authenticated:
        return redirect("/login")
    return dashboard_layout()
```

### Enhanced Type Validation
Full type checking for query parameters and path variables with comprehensive error handling.

```python
from pydantic import BaseModel, Field

class UserQuery(BaseModel):
    period: str = Field(default="monthly", regex="^(daily|weekly|monthly|yearly)$")
    limit: int = Field(default=10, ge=1, le=100)

async def layout(query: UserQuery, **kwargs):
    # Automatic validation and type conversion
    return render_dashboard(query)
```

### Manual Route Injection
Install and inject existing Dash applications into the routing system.

```python
from dash_router import Router
from my_existing_app import create_dashboard

router = Router(app)
router.inject_app("/dashboard", create_dashboard)
```

### Page Wrapper Components
Custom wrapper components for consistent layouts across routes.


### Modal Routes (Intercepting Routes)
Modal components that correspond to routes and update the URL when opened/closed, similar to Next.js intercepting routes.


**Use Cases:**
- Product detail modals from product lists
- User profile modals from user mentions
- Quick edit forms without page navigation
- Preview modals with full route state

## Setup

### Example app structure

```
├── app/
├── pages/                              -> Root Route
│   ├── page.py                         -> Root page (/)
│   ├── sales/                          -> Nested Route
│   │   ├── page.py                     -> /sales
│   │   ├── _components/                -> Shared components
│   │   ├── overview/
│   │   │   └── page.py                 -> /sales/overview
│   │   ├── analytics/
│   │   │   ├── page.py                 -> /sales/analytics
│   │   │   ├── components.py           -> Shared components
│   │   │   └── (figures)/              -> Slot route
│   │   │       ├── page.py             -> /sales/analytics
│   │   │       ├── loading.py          -> Loading state
│   │   │       ├── (figure_1)/
│   │   │       │   ├── page.py
│   │   │       │   └── api.py
│   │   │       ├── (figure_2)/
│   │   │       │   ├── page.py
│   │   │       │   └── api.py
│   │   │       ├── (figure_3)/
│   │   │       │   ├── page.py
│   │   │       │   └── api.py
│   │   │       ├── (figure_4)/
│   │   │       │   ├── page.py
│   │   │       │   └── api.py
│   │   │       └── (figure_5)/
│   │   │           ├── page.py
│   │   │           └── api.py
│   │   ├── dashboard/
│   │   │   ├── page.py                 -> /sales/dashboard
│   │   │   ├── api.py                  -> Data endpoint
│   │   │   ├── models.py               -> Data models
│   │   │   ├── components/             -> Shared components
│   │   │   ├── (ranks)/
│   │   │   │   ├── page.py
│   │   │   │   ├── api.py
│   │   │   │   ├── components.py
│   │   │   │   └── loading.py
│   │   │   ├── (revenue)/
│   │   │   │   ├── page.py
│   │   │   │   ├── api.py
│   │   │   │   ├── components.py
│   │   │   │   └── loading.py
│   │   │   └── (sentiment)/
│   │   │       ├── page.py
│   │   │       ├── api.py
│   │   │       ├── components.py
│   │   │       └── loading.py
│   │   └── invoices/
│   │       ├── page.py                 -> /sales/invoices
│   │       ├── components.py           -> Shared components
│   │       ├── (overview)/             -> Slot route
│   │       │   ├── page.py
│   │       │   ├── api.py
│   │       │   └── loading.py
│   │       └── [invoice_id]/           -> Path template
│   │           ├── page.py             -> /sales/invoices/<invoice_id>
│   │           ├── api.py              -> Data endpoint
│   │           ├── loading.py          -> Loading state
│   │           ├── items/
│   │           │   ├── page.py
│   │           │   ├── api.py
│   │           │   ├── error.py        -> Error handling
│   │           │   └── loading.py
│   │           ├── positions/
│   │           │   ├── page.py
│   │           │   ├── api.py
│   │           │   └── loading.py
│   │           └── conversation/
│   │               └── page.py
│   ├── nested_route/                   -> Complex nested example
│   │   ├── page.py
│   │   ├── components.py
│   │   ├── callback.py
│   │   ├── (slot_1)/                   -> Slot route
│   │   │   └── page.py
│   │   ├── (slot_2)/                   -> Slot route
│   │   │   └── page.py
│   │   ├── child_1/
│   │   │   └── page.py
│   │   ├── child_2/
│   │   │   ├── page.py
│   │   │   ├── api.py
│   │   │   └── components.py
│   │   └── child_3/
│   │       ├── page.py
│   │       ├── components.py
│   │       ├── models.py
│   │       ├── (slot_31)/
│   │       │   ├── page.py
│   │       │   ├── api.py
│   │       │   └── loading.py
│   │       ├── (slot_32)/
│   │       │   ├── page.py
│   │       │   ├── api.py
│   │       │   └── loading.py
│   │       ├── (slot_33)/
│   │       │   ├── page.py
│   │       │   ├── api.py
│   │       │   └── loading.py
│   │       ├── (slot_34)/
│   │       │   ├── page.py
│   │       │   ├── error.py
│   │       │   └── loading.py
│   │       └── (slot_35)/
│   │           ├── page.py
│   │           ├── api.py
│   │           └── loading.py

│   └── files/
│       ├── page.py                     -> /files
│       └── [__rest]/                   -> Catch-all route
│           ├── page.py
│           └── components.py
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

## Data Injection

- The router automatically collects and executes data functions before rendering layouts
- Data is injected into layout functions as the `data` argument
- This enables data-centric development where your layouts focus on presentation

```python
# pages/sales/dashboard/page.py
from dash_router import RouteConfig
import dash_mantine_components as dmc


config = RouteConfig(title="Dashboard")

async def layout(data: dict, **kwargs):
    return dmc.Stack([
        dmc.Title("Sales Dashboard"),
        dmc.SimpleGrid([
            dmc.Card([
                dmc.Text("Revenue", size="sm", c="dimmed"),
                dmc.Title(f"${data['revenue']:,}", order=3, c="green")
            ]),
            dmc.Card([
                dmc.Text("Orders", size="sm", c="dimmed"),
                dmc.Title(str(data['orders']), order=3, c="blue")
            ]),
            dmc.Card([
                dmc.Text("Customers", size="sm", c="dimmed"),
                dmc.Title(str(data['customers']), order=3, c="orange")
            ]),
            dmc.Card([
                dmc.Text("Growth", size="sm", c="dimmed"),
                dmc.Title(f"{data['growth']}%", order=3, c="teal")
            ])
        ], cols=4)
    ])
```

```python
# pages/sales/dashboard/api.py
from api.sql_operator import db_operator
from api.models.amazon import AmazonProduct
from ..models import AmazonQueryParams, SalesCallbackParams
from ..api import (
    apply_amazon_filters,
    get_date_granularity_column,
    get_agg_variant_column,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import pandas as pd
import asyncio

NAMESPACE = "example-dashboard"
TTL = 60 * 5


@db_operator(verbose=True)
async def endpoint(db: AsyncSession, **kwargs):
    variant = kwargs.pop("variant", SalesCallbackParams.get_default_variant())
    filters = AmazonQueryParams(**kwargs)
    agg_col = get_agg_variant_column(variant)
    date_col, _ = get_date_granularity_column(
        filters.granularity, AmazonProduct.SaleDate
    )
    query = select(
        AmazonProduct.MainCategory,
        date_col.label("Date"),
        agg_col.label("ProductCount"),
    )

    query = apply_amazon_filters(query, filters)
    query = query.group_by(date_col, AmazonProduct.MainCategory)
    query = query.order_by(desc("ProductCount"))
    result = await db.execute(query)
    data = pd.DataFrame(result)
    data = data.pivot(index="Date", columns="MainCategory", values="ProductCount")
    data = data.fillna(0)
    return data

```

## Create Nested Routes

- Routes and their folders are automatically nested routes
- Nested routes get passed as `ChildContainer` to their parent layout
- Parent layout defines the position of all child segments
- ChildContainer have a special property `props` with the `active` attribute which contains the name of the active children
- Set default child routes with `default_child`
- _upcoming version will have a method to securely create urls in your layout_

```python
# pages/sales/page.py -> /sales
from ._components.tabs import Tabs

from dash_router import ChildContainer, RouteConfig
import dash_mantine_components as dmc


config = RouteConfig(default_child="overview", title="Sales")

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

## Static Routes

- Set `is_static=True` in the `RouteConfig` to render the layout as root without any children
- Static routes utilize native mapping with path template support
- Useful for standalone pages that don't need nested routing

```python
# pages/about/page.py -> /about
from dash_router import RouteConfig
import dash_mantine_components as dmc


config = RouteConfig(
    title="About",
    is_static=True
)

async def layout(**kwargs):
    return dmc.Stack([
        dmc.Title("About Our Company", order=1),
        dmc.Text("Welcome to our sales analytics platform."),
        dmc.Space(h=20),
        dmc.Card([
            dmc.Title("Features", order=3),
            dmc.List([
                dmc.ListItem("Real-time analytics"),
                dmc.ListItem("Interactive dashboards"),
                dmc.ListItem("Advanced reporting")
            ])
        ])
    ])
```

**Static route with path template**:

```python
# pages/profile/[user_id]/page.py -> /profile/<user_id>
from dash_router import RouteConfig
import dash_mantine_components as dmc


config = RouteConfig(
    path_template="<user_id>",
    is_static=True,
    title="User Profile"
)

async def layout(user_id: str, **kwargs):
    return dmc.Stack([
        dmc.Title(f"Profile: {user_id}", order=1),
        dmc.Card([
            dmc.Title("User Information", order=3),
            dmc.Text(f"User ID: {user_id}"),
            dmc.Text("This is a static route with path parameters")
        ])
    ])
```

## Create Slots

- Slots are silent route segments with the behaviour of a normal nested route
- Positions also get managed by their parent layout
- Slots are independent from each other and executed in parallel (Flash only)

**Parent Route**:

```python
# pages/sales/invoices/page.py -> /sales/invoices
from ._components.table import create_invoice_table

from dash_router import SlotContainer
import dash_mantine_components as dmc


async def layout(vendors: SlotContainer, invoice: SlotContainer, data: dict, **kwargs):

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

**Basic Slot**:

```python
# pages/sales/invoices/(vendors)/page.py -> /sales/invoices
from ._components.figures import create_barchart


async def layout(data: dict, **kwargs):
    return create_barchart(data)
```

**Slot with Loading State**:

```python
# pages/sales/analytics/(figures)/loading.py
import dash_mantine_components as dmc


def layout(**kwargs):
    return dmc.Card(
        dmc.Loader(size="md", color="blue"),
        p="xl",
        withBorder=True,
        style={"textAlign": "center"}
    )
```

```python
# pages/sales/analytics/(figures)/page.py
from dash_router import RouteConfig
import dash_mantine_components as dmc
import plotly.express as px


config = RouteConfig(title="Analytics Figures")

async def layout(data: dict, **kwargs):
    
    return dmc.Stack([
        dmc.Title("Sales Analytics", order=2),
        dmc.SimpleGrid([
            dmc.Card(
                dmc.Stack([
                    dmc.Title("Revenue Trend", order=4),
                    px.line(data, x="day", y="total_bill", title="Daily Revenue")
                ])
            ),
            dmc.Card(
                dmc.Stack([
                    dmc.Title("Sales Distribution", order=4),
                    px.histogram(data, x="total_bill", title="Sales Distribution")
                ])
            )
        ], cols=2)
    ])
```

## Path Variables

- Path variables can be applied on static and slot routes
- Path templates in dynamic routes have to be slots
- Get defined in the RouteConfig and contain <>
- Static routes can have multiple kwargs in a path template, slots only take one kwarg
- _upcoming version will have type conversions and a <...rest> template that takes all remaining segments as arguments_

**Slot with path variable**:

```python
# pages/sales/invoices/[invoice_id]/page.py -> /sales/invoices/<invoice_id>
from ._components.figures import create_comp_chart
from ._components.tabs import create_invoice_tabs

from dash_router import RouteConfig, ChildContainer


config = RouteConfig(default_child="items")

async def layout(children: ChildContainer, invoice_id: int = None, data: dict = None, **kwargs):

    # Deal with defaults:
    if not invoice_id:
        return dmc.Stack(
            [
                dmc.Icon("carbon:select-01", size=60),
                dmc.Title("No invoice selected", order=3),
            ],
            align="center"
        )

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
# pages/monitoring/[cid]/page.py -> /monitoring/<cid>
import dash_mantine_components as dmc
from dash_router import RouteConfig


config = RouteConfig(is_static=True)

async def layout(cid: str, **kwargs):
    return dmc.Title(f"Monitoring {cid}")
```

**Multiple path variables in static route**:

```python
# pages/monitoring/[cid]/[unit]/[other_id]/page.py -> /monitoring/<cid>/unit/<other_id>
import dash_mantine_components as dmc
from dash_router import RouteConfig


config = RouteConfig(is_static=True)

async def layout(cid: str, unit: str, other_id: str, **kwargs):
    return dmc.Title(f"Monitoring {cid} {unit} {other_id}")
```

## Catch-All Routes

- Use `[__rest]` folder name to create catch-all routes that match any remaining path segments
- Useful for file viewers, documentation, or fallback pages

```python
# pages/files/[__rest]/page.py -> /files/*
from dash_router import RouteConfig
import dash_mantine_components as dmc


config = RouteConfig()

async def layout(rest: list, **kwargs):
    return dmc.Stack([
        dmc.Title("File Viewer", order=2),
        dmc.Alert(
            f"Requested path: {path}",
            title="Path Information",
            color="blue"
        ),
        dmc.Text(f"This is a catch-all route that handles any path under /files/")
    ])
```

## Error Layouts

- Add `error.py` file to your route folder with DashComponent or function named layout for custom error handling
- Layout receives the exception as well as the path variables and search params the layout used
- A basic red card with the error message gets displayed by default

```python
# pages/sales/invoices/[invoice_id]/items/error.py
import dash_mantine_components as dmc


def layout(e: Exception, *args, **kwargs):
    return dmc.Alert(
        str(e),
        title="Error occurred",
        color="red",
        variant="light"
    )
```

**Advanced Error Handling**:

```python
# pages/sales/invoices/[invoice_id]/items/error.py
import dash_mantine_components as dmc
from typing import Optional


def layout(e: Exception, invoice_id: Optional[str] = None, *args, **kwargs):
    error_message = str(e)
    
    if "not found" in error_message.lower():
        return dmc.Alert(
            f"Invoice {invoice_id} not found",
            title="Invoice Not Found",
            color="yellow",
            variant="light",
            icon=dmc.Icon("carbon:warning")
        )
    
    return dmc.Alert(
        error_message,
        title="Unexpected Error",
        color="red",
        variant="light",
        icon=dmc.Icon("carbon:error")
    )
```

## Query Parameters

- URL query parameters automatically update the UI based on layout function input params
- Supports Pydantic models and basic Python types for type checking
- Parameters are automatically converted to the correct type
- **Note**: Currently only one-level Pydantic models are supported

```python
# pages/sales/analytics/page.py -> /sales/analytics?period=monthly&region=us
from dash_router import RouteConfig
import dash_mantine_components as dmc
from typing import Optional
from enum import Enum


class Period(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


config = RouteConfig(title="Analytics")

async def layout(
    period: Period = Period.MONTHLY,
    region: str = "us",
    limit: int = 10,
    **kwargs
):
    return dmc.Stack([
        dmc.Title("Sales Analytics", order=2),
        dmc.Alert(
            f"Showing {period.value} data for {region} (limit: {limit})",
            title="Current Filters",
            color="blue"
        ),
        dmc.SimpleGrid([
            dmc.Card(
                dmc.Stack([
                    dmc.Title("Revenue Chart", order=4),
                    dmc.Text(f"Period: {period.value}"),
                    dmc.Text(f"Region: {region}"),
                    dmc.Text(f"Limit: {limit}")
                ])
            )
        ])
    ])
```

**Pydantic Model Example**:

```python
# pages/sales/analytics/page.py -> /sales/analytics?period=monthly&region=us&limit=20
from dash_router import RouteConfig
import dash_mantine_components as dmc
from pydantic import BaseModel
from enum import Enum


class Period(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AnalyticsQuery(BaseModel):
    period: Period = Period.MONTHLY
    region: str = "us"
    limit: int = 10


config = RouteConfig(title="Analytics")

async def layout(query: AnalyticsQuery, **kwargs):
    return dmc.Stack([
        dmc.Title("Sales Analytics", order=2),
        dmc.Alert(
            f"Showing {query.period.value} data for {query.region} (limit: {query.limit})",
            title="Current Filters",
            color="blue"
        ),
        dmc.SimpleGrid([
            dmc.Card(
                dmc.Stack([
                    dmc.Title("Revenue Chart", order=4),
                    dmc.Text(f"Period: {query.period.value}"),
                    dmc.Text(f"Region: {query.region}"),
                    dmc.Text(f"Limit: {query.limit}")
                ])
            )
        ])
    ])
```


