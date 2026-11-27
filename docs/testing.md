# Testing routes

`dash_router.testing` checks what a navigation renders without a server or a browser. A test states an old URL, a new URL and the nodes that should render. Tests run in milliseconds.

## Test your real app

```python
# tests/test_routes.py
import asyncio

import pytest

from dash_router import ChildContainer, RouteTester, SlotContainer


@pytest.fixture(scope="module")
def tester() -> RouteTester:
    import app  # builds the Dash app and the DashRouter

    return RouteTester(app.router)


def test_first_load(tester):
    tester.assert_routes(old=None, new="/", expected=["/", "overview", "overview/(kpis)", "overview/(revenue)"])


def test_query_change_rerenders_one_slot(tester):
    result = tester.assert_routes(old="/overview", new="/overview?range=7d", expected=["overview/(revenue)"])
    assert result.targets == [SlotContainer.ids.container("overview", "revenue")]


def test_selecting_an_order_keeps_the_list(tester):
    result = tester.assert_routes(
        old="/orders?status=delayed",
        new="/orders/1003?status=delayed",
        expected=["orders/[order_id]", "orders/[order_id]/summary"],
        expected_vars={"orders/[order_id]": {"order_id": "1003"}},
    )
    assert result.targets == [ChildContainer.ids.container("orders")]
```

You can also build the tester from a folder without creating a Dash app: `RouteTester.from_folder("pages")`.

## `assert_routes`

```python
tester.assert_routes(
    old: str | None,          # None = fresh page load
    new: str,
    expected: Iterable[str],  # node ids that must render, nothing more and nothing less
    *,
    ordered=False,            # True: compare as an ordered list
    expected_modes=None,      # {"node_id": "page" | "default" | "empty"}
    expected_vars=None,       # {"node_id": {"var": value}}: a subset of the node's variables
    extra_inputs=None,        # values of app.routing_callback_inputs for the new URL
    prev_extra_inputs=None,   # ... and for the old URL
) -> TransitionResult
```

It raises `AssertionError` with the missing and unexpected node ids and the patched containers. It also fails if a node would render twice in one transition. `assert_transition(target, old, new, expected, **checks)` is the same as a function, where `target` is a `DashRouter`, a `RouteTree` or a `RouteTester`, and the checks are passed on to `assert_routes`.

Path variables in `expected_vars` are the raw URL strings (`"1003"`). Coercion to `int` happens when the layout is called.

## `TransitionResult`

`tester.transition(old, new)` returns the result without asserting anything:

| Attribute | Meaning |
| --- | --- |
| `matched` | `False` when the new URL is not found |
| `segments` | node ids that render, in render order |
| `targets` | ids of the patched containers |
| `modes` | render mode (`page`, `default` or `empty`) of every node the transition patches |
| `vars` / `vars_for(node_id)` | variables (query values and path variables) per rendered node |
| `plan` | the underlying `TransitionPlan` |
| `await render()` | runs endpoints and layouts eagerly and returns the container updates. Boundaries are loaded in full, so there are no skeletons |

```python
def test_pinned_slot_is_empty(tester):
    tester.assert_routes(
        old="/customers/accounts/3",
        new="/customers/insights",
        expected=["customers/insights", "customers/(inspector)"],
        expected_modes={"customers/(inspector)": "default", "customers/(pinned)": "empty"},
    )


def test_error_boundary_renders(tester):
    updates = asyncio.run(tester.transition(None, "/overview?fail=activity").render())
    ...
```

`render` really runs your endpoints, including their delays and I/O. Use it for a few smoke tests and keep the bulk of the tests on `segments`, `modes` and `targets`. Tests only see the plan; the streaming of boundaries is not part of `RouteTester` ([Browser tests](#browser-tests)).

## Inline route specs

To test routing rules on their own, describe the tree as a dict. No files or layouts are needed:

```python
tester = RouteTester.from_spec({
    "/": {"accepts_children": True, "default_child": "tickets"},
    "tickets": {
        "[ticket_id]": {
            "(detail)": {"(summary)": {}},
            "(activity)": {"inputs": ["filter"], "(comments)": {}},
        }
    },
})

tester.assert_routes(
    old="/tickets/1001",
    new="/tickets/1001?filter=unread",
    expected=["tickets/[ticket_id]/(activity)", "tickets/[ticket_id]/(activity)/(comments)"],
)
```

Each key is a folder name (`"tickets"`, `"[ticket_id]"`, `"(detail)"`, `"[__rest]"`). Each value is a dict of child folders plus these optional settings:

| Key | Meaning |
| --- | --- |
| `layout` | A layout. Without it, a generated layout renders the node id, `data`, slots and children. `False` makes the node a passthrough. |
| `endpoint` | An `api.py` endpoint function. |
| `loading`, `error`, `default` | Layouts, or `True` for a generated placeholder. |
| `inputs` | Extra query parameters the node subscribes to (in addition to its signatures). |
| `default_child`, `is_static`, `title` | As in `RouteConfig`. |
| `accepts_children` | Force whether the node takes `children`. The generated layout takes `children` only when the node has nested child keys, so a root that should act as a shell around the top-level keys needs `"accepts_children": True`. |

`DashRouter.from_spec(spec, app=None, not_found_layout=None)` builds a full router from the same format, and `RouteTree.from_spec(spec)` builds just the tree. A spec lists its folders directly, so the spec builders take no `ignore_empty_folders`.

## Browser tests

`RouteTester` covers which nodes render. To check the real page (streaming order, skeletons, document titles), run the app and drive it with a browser tool such as Playwright or `dash.testing`. The showcase's rendered badges and Transition log make useful assertions: a badge that keeps its time was not re-rendered.
