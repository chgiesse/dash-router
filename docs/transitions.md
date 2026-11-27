# Transitions and streaming

This page explains what happens between a URL change and the updated page. You do not need it to use the router, but it explains why a part of the page re-renders or keeps its content.

## Planning: diffing two matched trees

For every navigation the router matches **both** the old and the new URL, then walks the two matched trees from the top:

- Two nodes are the same when they have the same node id, the same render mode (`page`, `default`, or `empty`), the same path variables and the same subscribed query values. The router keeps the node and compares its `children` and slots next.
- When they differ, the container that holds the node gets the new node and **everything inside it**. The router does not look further down.
- A slot that no longer matches the URL is patched too. It shows its `default.py`, or nothing (`empty`). Nothing keeps its old content.

The result is a list of container patches. Some examples from the showcase:

| Transition | Patched container | Rendered nodes |
| --- | --- | --- |
| `/overview` -> `/orders` | `children` of `/` | `orders`, `orders/[order_id]`, `orders/(listing)` |
| `/overview` -> `/overview?range=7d` | slot `revenue` of `overview` | `overview/(revenue)` |
| `/orders` -> `/orders/1003` | `children` of `orders` | `orders/[order_id]` (header + tabs, at once), `orders/[order_id]/summary` (behind `summary/loading.py`) |
| `/orders/1003` -> `/orders/1003/timeline` | `children` of `orders/[order_id]` | `orders/[order_id]/timeline` |
| `/orders?status=delayed` -> `/orders/1003?status=delayed` | `children` of `orders` | `orders/[order_id]`, `orders/[order_id]/summary` |
| `/orders/1003` -> `/orders/1003?status=open` | slot `listing` of `orders` | `orders/(listing)` |
| `/customers/accounts/3` -> `/customers/insights` | `children` and slot `inspector` of `customers`, slot `pinned` of `customers` | `customers/insights`, `customers/(inspector)` (`default`); `customers/(pinned)` is `empty` |
| `/overview` -> `/status` (static) | the whole page | `status` |
| fresh page load | the whole page | every matched node |

`router.plan(old_url, new_url)` returns this plan. `RouteTester` shows it in tests ([Testing routes](testing.md)).

## Two responses per navigation

A navigation has two parts:

1. **The navigation response.** One plain callback plans the transition, runs every endpoint outside a lazy boundary, and returns the patched containers together with the committed URL store (`url`, `seq`, `extra` and the page `title`). Dash applies them together.
2. **Lazy boundaries.** A `loading.py` boundary and a generator layout (a layout that uses `yield` or is an `async def` generator) are not rendered in the response. The response contains a `LazyContainer` in their place, holding the `loading.py` skeleton (or nothing, when there is no `loading.py`). Each `LazyContainer` then runs its own streaming callback. That callback runs the boundary's endpoint, its layout and everything below it down to the next boundary, and sends the result when it is ready.

A generator layout streams several frames: each `yield` sends an update, and a bare `yield` sends a flush without replacing what is already on screen. The browser runs the initial calls of any newly mounted callbacks, including no-output callbacks (see [Layouts](layouts.md#callbacks-inside-routes)).

A navigation with two boundaries therefore looks like this:

- The click sends the navigation. The response arrives with the new page and the skeletons.
- Each boundary's stream starts when its `LazyContainer` mounts and replaces its skeleton when it finishes. The streams run independently, in the order they finish.

Streaming `LazyContainer`s require the Risk Shield patched `dash-renderer` (`packages/dash`). Plain navigation, without boundaries, works on stock Dash.

## Loading states come from the server

The browser does not route. Every change of the router's location, including one that only touches a slot, goes to the server, and the server decides what renders. The browser has no copy of the route tree and no skeletons of its own.

A loading state therefore appears after one roundtrip: the skeleton of a lazy boundary is part of the navigation response. Every `loading.py` boundary shows its skeleton first, even when its data is already cached. A node that has no `loading.py` and is not a generator shows nothing new until its endpoint is done, because it is part of the response ([Without `loading.py`](data-loading.md#loadingpy-skeletons-and-lazy-boundaries)).

The server also decides the rules that need the full route, such as typed query defaults, the `default.py` of an unmatched slot and skeletons that take arguments.

## Superseded navigations

If you navigate again while a page is still loading, the newer navigation wins:

- Only the newest navigation response is applied. An outdated response is discarded by Dash, and the committed store is written together with the containers, so a slow earlier navigation cannot overwrite a newer one.
- A `LazyContainer` that a newer navigation replaces or unmounts is dropped. Its stream results and frames are ignored, and the patched `dash-renderer` aborts its stream. That closes the generator on the server, on whichever worker or pod runs it, with no shared storage between pods.
- A `LazyContainer` that the newer navigation does not touch stays mounted and keeps streaming. Its boundary is not re-rendered, and a generator that is not patched is not restarted.

Example: on `/overview`, the Activity slot takes 3.5 s and the live feed streams for about 9 s. Switching to `/overview?range=7d` after 0.5 s re-renders only Revenue, because Activity and the live feed do not subscribe to `range`. Both keep loading in place. If the switch had changed their container or their subscriptions, they would be replaced and their streams aborted.

## Debugging

- Each card in the showcase shows a `rendered HH:MM:SS.mmm` badge. If the badge did not change after a navigation, that node was not re-rendered.
- `router.plan(old, new).segments` lists the nodes a transition renders, and `.targets` lists the patched containers. Nodes in `empty` mode are patched but not listed in `segments`.
