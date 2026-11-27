# Troubleshooting

## A part of the page is replaced more than expected, or never appears

The layout around it did not render the container it received. The router patches containers by id. If a patch targets a container that is not on the page (for example, its parent is still showing a skeleton or omitted its `ChildContainer`), the router replaces the nearest container that is on the page instead, and drops the patches that this covers. A missing container therefore updates its parent, rather than being lost. A parent that replaces more than you expected is usually the cause.

Render `children` and every slot argument in every branch of the layout, and show placeholders next to them ([Rule 1](layouts.md#rule-1-always-render-the-containers-you-receive)).

## A node does not re-render when a query parameter changes

The node does not subscribe to that parameter. Only arguments declared in the node's route function or `endpoint` signature count ([Subscriptions](query-params.md#subscriptions-who-re-renders)):

- Reading the value from `**kwargs` does not subscribe.
- Annotations that are not plain types (for example `datetime.date`) are not treated as query parameters. Use `str` and parse the value yourself, or use a Pydantic model field.
- Changing a value to its default (`?page=1` with `page: int = 1`) is not a change.

## A node re-renders more often than expected

When a node re-renders, everything inside it renders again too. If a parent subscribes to a parameter that only one child needs, move the parameter to the child. Check with `router.plan(old, new).segments` or a `RouteTester` test.

## A `[param]` in a slot matches the wrong URLs

A bare `[param]` folder matches any single segment, including `segments` or `insights`. Inside slots, put a static folder in front: `(inspector)/accounts/[customer_id]` ([details](parallel-routes.md#put-a-static-prefix-in-front-of-param-in-slots)).

## A slot is empty after a navigation

A route slot has no route for this URL and no `default.py`. The slot renders empty and its previous content is removed. Slots do not keep content from an earlier URL. Add a `default.py` to the slot to show something instead ([details](parallel-routes.md#when-a-slot-has-no-match)).

## A URL is "not found" although a slot seems to match it

A URL is valid when the main branch matches it, or when at least one route slot matches it. A slot's own routes match only its own branch. Check the route folder names, and for `[param]` folders in slots, the static prefix ([details](parallel-routes.md#put-a-static-prefix-in-front-of-param-in-slots)).

## A layout receives a component instead of a query value

A slot has the same name as the query parameter. Rename the slot ([details](parallel-routes.md#do-not-name-a-slot-like-a-query-parameter)).

## The navigation response is slow

An `api.py` outside any lazy boundary must finish before the navigation response is sent. Add a `loading.py` next to it ([details](data-loading.md#loadingpy-skeletons-and-lazy-boundaries)).

## The skeleton appears late

A skeleton arrives with the navigation response, one roundtrip after the click or the page load. Everything outside a lazy boundary must finish before that response is sent, so a slow endpoint without a `loading.py` delays the skeleton of its siblings too ([details](data-loading.md#loadingpy-skeletons-and-lazy-boundaries)).

## A skeleton never gets replaced, or a generator keeps running

A lazy boundary's stream replaces its skeleton when it finishes. A failing endpoint or layout replaces the skeleton with the node's `error.py` (or the default error banner), so a skeleton that stays is usually a slow endpoint or a renderer that does not stream ([requirements](getting-started.md#requirements)).

A generator layout runs until it returns. A navigation that does not patch its container leaves it running, so it keeps streaming while it is on screen. To stop it, navigate to a URL that replaces or unmounts its container. The patched `dash-renderer` then aborts the stream and the server closes the generator ([details](transitions.md#superseded-navigations)).

## Lazy boundaries or generators do not stream

Streaming `LazyContainer`s need the Risk Shield patched `dash-renderer` (`packages/dash`). Plain navigation works on stock Dash, but boundaries and generator layouts are only streamed by the patched renderer. Check that the app serves the patched renderer ([requirements](getting-started.md#requirements)).

## `get_current_url()` returns `/` inside a layout

Layouts and endpoints of deferred subtrees (`loading.py` boundaries and generator layouts) run inside their own streaming callback. There the browser sends the stream worker's script as `Referer`, so `get_current_url()` falls back to `/`. Read the values you need from the layout's arguments (path variables and query values), or take `State(RootContainer.ids.location, "href")` in your own callbacks ([details](navigation.md#reading-the-current-url)).

## A callback in a route never runs

- Check that the module defining it is imported: callbacks in `page.py`, `callbacks.py` or `callback.py` are imported automatically. Callbacks in other files need to be imported by one of those.
- `prevent_initial_call=True` skips the call when the content mounts, as on a normal page.
- Component ids must be unique among everything on screen. A slot and the main branch can be visible at the same time.
- `suppress_callback_exceptions=True` must be set on the app.

## A warning: a route renders a child, but its layout does not place `children`

```text
Route 'orders' renders a child route, but its layout does not place `children`. ...
```

The router logs this once per node, on the `dash_router` logger, when a child route matches but the layout did not place its `ChildContainer`, so the child is not on the page. Take `children` in the layout and render it where the child should appear.

The warning is only logged for a child that matched. Visiting `/edge-cases/omitted-child/sub?mode=blocked` in the showcase logs it once, because that layout hides its children on purpose to show the case.

## Startup errors

| Error | Fix |
| --- | --- |
| `RouteModuleImportError` | The message names the file and the original exception. Fix the import in that file. |
| `RouteLayoutMissingError` | Define the role name in the named file (`page` in `page.py`, `loading` in `loading.py`, `error` in `error.py`, `default` in `default.py`; `layout` also works in any of them). |
| `RouteConfigConflictError` | Remove either the `RouteConfig` field or the file (`loading.py`, `error.py`, `default.py`), or keep one of the role name and `layout` in a route file. |
| `RouteTreeValidationError` | Fix `default_child` to name an existing child folder, remove children or slots from an `is_static` route, or move child routes out of a catch-all. |
| `ValueError: ... already defines dynamic child` | A node has two `[param]` / `[__rest]` folders. Keep one, or put a static prefix in front of the other. |

