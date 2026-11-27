# API reference

Everything below is importable from `dash_router` (the list is `dash_router.__all__`). The router needs an async backend: Quart or FastAPI.

## `DashRouter`

```python
DashRouter(
    app: Dash | None = None,
    pages_folder: str | Path = "pages",
    *,
    tree: RouteTree | None = None,
    not_found_layout: ErrorLayout | ComponentTree | None = None,
    ignore_empty_folders: bool = False,
    generate_stubs: bool | None = None,
    stubs_dir: Path | None = None,
)
```

| Parameter | Meaning |
| --- | --- |
| `app` | The Dash app. The router registers its callbacks on it and sets `app.router`. Without an app you get a router for planning and tests only. |
| `pages_folder` | The pages folder. A relative path is tried as given, then from the app's `pages_folder` setting, then next to the app's module. |
| `tree` | Use a prebuilt `RouteTree` instead of scanning a folder. |
| `not_found_layout` | Component or function rendered for unknown URLs. |
| `ignore_empty_folders` | `True`: folders without `page.py` do not add a URL segment ([details](routing.md#static-prefixes-accountscustomer_id)). |
| `generate_stubs`, `stubs_dir` | Write typed `url_for` stubs under `typings/dash_router-stubs/`. Defaults to `True` for folder-loaded routers and `False` for `from_spec` ([details](navigation.md#typed-route-ids-and-inputs)). |

If the app defines `on_error`, it is used as the error layout of nodes without an `error.py`.

Each navigation is one plain callback. Its `loading.py` boundaries and generator layouts load through streaming callbacks of their own ([Transitions](transitions.md#two-responses-per-navigation)).

| Method or attribute | Meaning |
| --- | --- |
| `DashRouter.from_spec(spec, app=None, not_found_layout=None, *, generate_stubs=None, stubs_dir=None)` | Build from an inline spec ([details](testing.md#inline-route-specs)). |
| `reload()` | Re-scan `pages_folder` and refresh route metadata and `url_for` stubs. |
| `tree` | The `RouteTree`. `tree.nodes` maps node ids to `RouteNode`. |
| `match(url, extra_inputs=None)` | The `MatchedTree` for a URL, or `None` if not found. |
| `plan(old_url, new_url, extra_inputs=None, prev_extra_inputs=None)` | The `TransitionPlan` of a navigation. |

## `RouteConfig`

Define `config = RouteConfig(...)` in a `page.py`. Every field is stored on the node as `node.config.<field>`.

| Field | Type | Meaning |
| --- | --- | --- |
| `default_child` | `str \| None` | Child folder rendered when the URL stops at this node ([details](routing.md#when-the-url-stops-at-a-parent)). |
| `is_static` | `bool` | Render without the shell ([details](routing.md#standalone-pages-is_statictrue)). |
| `title` | `str \| Callable \| None` | Document title, a string or a function of the route variables ([details](navigation.md#page-titles)). |
| `default` | layout | Inline `default.py`. |
| `loading` | layout | Inline `loading.py`. |
| `error` | error layout | Inline `error.py`. |
| `description`, `name`, `order`, `image`, `image_url`, `redirect_from`, `meta` | | Stored on the node for your own use. The router does not act on them. |

## Naming

Each route file defines a function or component named after the file. `layout` is still accepted in every file as a fallback:

| File | Name | Fallback |
| --- | --- | --- |
| `page.py` | `page` | `layout` |
| `loading.py` | `loading` | `layout` |
| `error.py` | `error` (receives the exception as its first argument) | `layout` |
| `default.py` | `default` | `layout` |
| `api.py` | `endpoint` | — |

Defining both the role name and `layout` in the same file raises `RouteConfigConflictError`. `RouteTree.from_spec` keys (`layout`, `default`, `loading`, `error`, `endpoint`) are unchanged.

## Route files

| File | Must define | Called with |
| --- | --- | --- |
| `page.py` | `page` or `layout` (component or function), optional `config` | containers, `data`, path variables, query values |
| `api.py` | `endpoint` (function or async function) | path variables, query values |
| `loading.py` | `loading` or `layout` | path variables, query values |
| `error.py` | `error` or `layout` | the exception (first positional argument), path variables, query values |
| `default.py` | `default` or `layout` | path variables, query values |
| `callbacks.py`, `callback.py` | anything | imported at startup |

## Containers

| Class | Passed to layouts as | Notes |
| --- | --- | --- |
| `RootContainer(initial_children=None)` | — | Put once in `app.layout`. `RootContainer.ids` holds the ids of the location (`location`), the page container (`container`), the wrapper (`wrapper`) and the committed URL store (`committed_store`). |
| `ChildContainer(layout=None, parent_id="/", active=None, base=None)` | `children` | `.props.active` is the active child's URL segment. `.props.base` is the browser path of the parent, for example `/orders/1003`. Id: `ChildContainer.ids.container(parent_node_id)`. |
| `SlotContainer(layout=None, parent_id="/", slot_name="")` | the slot's name | Id: `SlotContainer.ids.container(parent_node_id, slot_name)`. |
| `LazyContainer(layout=None, lazy_key="", *, route=None)` | — | Holds a deferred subtree (a `loading.py` boundary or a generator layout) during navigation. `layout` is its skeleton (or `None`). `route` is the `data-route` payload `{node_id, url, extra?}` that its stream loads. The router creates these. |

## Components

Dash components that sync the page with the URL. They run in the browser, without callbacks ([Navigation](navigation.md#links), [Query parameters](query-params.md#urlparam-and-urlcommit)).

| Component | Signature | Meaning |
| --- | --- | --- |
| `Link` | `Link(children, href, *, replace=False, match="prefix")` | In-page link. Marks itself active with `aria-current="page"` and `data-active="true"`. `match="exact"` only matches the path itself. |
| `UrlSegment` | `UrlSegment(component, container=None, *, base=None, prop="value", default=None, history="push", keep_query=True)` | Syncs one prop of `component` (`value` of a tab bar) with the URL path segment after `base`. `container` is the layout's `ChildContainer`: its `props.base` and `props.active` are used unless `base=` is given. Choosing a value pushes `{base}/{value}`, the `default` value writes `base`. Back and forward update the prop ([details](navigation.md#tabs-in-the-url-urlsegment)). |
| `UrlParam` | `UrlParam(component, param, *, clear=None, prop="value", format="auto", default=..., history="push", debounce=0, two_way=False, group=None, commit_on=None, set_params=None)` | Syncs one prop of `component` with the query parameter `param`. |
| `UrlCommit` | `UrlCommit(component, group=None, *, prop="n_clicks", clear=None, set_params=None, history="push")` | Writes the values of a `group` of `UrlParam`s (or fixed `set_params`) when its child's `prop` changes. |

## Navigation

| Name | Signature | Meaning |
| --- | --- | --- |
| `navigate` | `navigate(url: str \| Url) -> None` | Navigate from any server callback ([details](navigation.md#navigate-from-a-callback)). |
| `url_for` | `url_for(route_id, params_or_model=None, **params) -> str` | Build a path (and query string) from a node id, path params, and declared query params/models. |
| `get_current_url` | `get_current_url(strict=False) -> Url` | The URL of the page that sent the current callback request ([details](navigation.md#reading-the-current-url)). |
| `Url` | `Url(pathname="/", search={})` | Immutable URL. `Url.parse(href)`, `to(pathname)`, `set_param`, `remove_param`, `update_params`, `clear_query`, `to_href()`. |

## Testing

| Name | Meaning |
| --- | --- |
| `RouteTester(target)` | Test harness for a `DashRouter` or a `RouteTree`. `RouteTester.from_folder(path, ignore_empty_folders=False)`, `RouteTester.from_spec(spec)` ([details](testing.md)). |
| `tester.transition(old, new, *, extra_inputs=None, prev_extra_inputs=None)` | Returns a `TransitionResult`. |
| `tester.assert_routes(old, new, expected, *, ordered=False, extra_inputs=None, prev_extra_inputs=None, expected_modes=None, expected_vars=None)` | Asserts the rendered nodes and returns a `TransitionResult`. |
| `assert_transition(target, old, new, expected, **checks)` | `RouteTester(target).assert_routes(old, new, expected, **checks)`. `target` is a `DashRouter`, `RouteTree` or `RouteTester`. |
| `TransitionResult` | `tree`, `plan`, `matched`, `segments`, `targets`, `modes`, `vars`, `vars_for(node_id)`, `await render()`. |

## Planning types

| Name | Meaning |
| --- | --- |
| `RouteTree` | The node tree. `RouteTree.from_folder(pages_folder, ignore_empty_folders=False)`, `RouteTree.from_spec(spec)`, `.nodes`. |
| `RouteNode` | One node: `node_id`, `kind` (`"root"`, `"route"`, `"param"`, `"catch_all"`, `"slot"`), `config` (a `RouteConfig`), `layout`, `default_layout`, `loading_layout`, `error_layout`, `endpoint`, `children`, `slots`, and `query` (the query parameters it subscribes to). |
| `MatchedTree`, `MatchedNode` | A URL matched against the tree. `MatchedTree` has `pathname`, `query_params`, `root`, `is_static`. `MatchedNode` has `node_id`, `kind`, `mode` (`"page"`, `"default"` or `"empty"`; `"empty"` is an unmatched slot without `default.py`), `active_segment`, `path_vars`, `subscribed_query`, `all_query`, `child`, `slots`, `omitted`, and `variables`, `walk()`, `find_node(node_id)`. |
| `TransitionPlan` | `old_url`, `new_url`, `old_tree`, `new_tree`, `patches`, and `matched`, `targets`, `segments`, `modes`, `node_vars`. `segments` leaves out `empty` nodes. |
| `PatchOp`, `PatchTarget` | One container patch (`subtree` is `None` when the container is cleared) and its target (`container_id`). |

## Errors

All of them are raised when the router builds the tree, so a broken route fails at startup instead of at the first visit. They live in `dash_router.errors` and are also exported from `dash_router`.

| Exception | Raised when |
| --- | --- |
| `RouteModuleImportError` | A route file fails to import. The message names the file. |
| `RouteLayoutMissingError` | A route file (`page.py`, `loading.py`, `error.py`, `default.py`) defines neither its role name nor `layout`. |
| `RouteConfigConflictError` | A layout is defined both in `RouteConfig` and as a file, or a route file defines both its role name and `layout`. |
| `RouteTreeValidationError` | `default_child` names a missing child, a static route has children or slots, or a catch-all has child routes. |
