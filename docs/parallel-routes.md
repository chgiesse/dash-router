# Slots and parallel routes

A folder named `(name)` is a **slot**. Slots render next to the node's `children`, in the same layout, and the parent receives each one as an argument named after the slot. A slot is a full node: it can have its own `page.py`, `api.py`, `loading.py`, `error.py`, nested slots and child routes.

There are two kinds of slots, and the router tells them apart automatically:

| Kind | The slot contains | It matches |
| --- | --- | --- |
| Passive slot | no child routes and no `[param]` folders (at any depth of nested slots) | whatever its parent matches. It always renders with its parent. |
| Route slot (parallel route) | child routes or `[param]` folders | the URL on its own, independently of the parent's `children` |

## Passive slots: independent panels on one page

```text
pages/overview/
├── page.py
├── (kpis)/      api.py · loading.py · page.py
├── (revenue)/   api.py · loading.py · page.py
└── (activity)/  api.py · loading.py · error.py · page.py
```

```python
# pages/overview/page.py
def page(kpis: SlotContainer, revenue: SlotContainer, activity: SlotContainer, **_):
    return html.Div([kpis, html.Div([revenue, activity], className="grid")])
```

The showcase's order list is a passive slot of `pages/orders/page.py`:

```python
# pages/orders/page.py
def page(children: ChildContainer, listing: SlotContainer, **_):
    return dmc.Grid([dmc.GridCol(listing, span=5), dmc.GridCol(children, span=7)])
```

The slot is rendered at `/orders` and at `/orders/<id>` alike, so the list stays put while the empty state (`[order_id]/default.py`) or an order changes in `children`.

Why split a page into slots instead of one big layout:

- **Parallel data.** Each slot's `api.py` starts at the same time.
- **Streaming.** With a `loading.py`, each slot shows its skeleton and streams in on its own as soon as it is ready. A slow panel does not hold up the others.
- **Isolated errors.** An `error.py` in a slot replaces only that slot.
- **Fine-grained updates.** A slot subscribes to its own query parameters. `?range=7d` re-renders only the slot that declares `range`.

A passive slot sees its parent's path variables and nothing else. It does not consume URL segments.

## Route slots: parallel routes

When a slot has child routes, it receives its own copy of the remaining URL segments and matches them separately from the parent's `children`. Two parts of the same page can then react to the same URL in different ways.

```text
pages/customers/
├── page.py                        page(children, inspector, pinned)
├── directory/page.py
├── segments/page.py
├── insights/page.py
├── accounts/[customer_id]/        main branch: the customer's page
│   ├── api.py
│   └── page.py
├── (inspector)/
│   ├── page.py                    wrapper around the slot's own `children`
│   ├── default.py                 shown when nothing in (inspector) matches
│   └── accounts/[customer_id]/    the inspector's view of the same customer
│       ├── api.py
│       ├── loading.py
│       └── page.py
└── (pinned)/                      no default.py
    ├── page.py
    ├── directory/page.py
    ├── segments/page.py
    └── accounts/[customer_id]/page.py
```

For `/customers/accounts/3` the remaining segments are `accounts/3`, and each branch matches them separately:

| Branch | Match | `customer_id` |
| --- | --- | --- |
| `children` | `customers/accounts/[customer_id]` | `3` |
| `(inspector)` | `customers/(inspector)/accounts/[customer_id]` | `3` (its own copy) |
| `(pinned)` | `customers/(pinned)/accounts/[customer_id]` | `3` (its own copy) |

All three endpoints run in parallel. A path variable matched in one branch is never visible in another.

A URL is valid when the main branch matches it, or when at least one route slot does. A route slot without a `page.py` is allowed. It then renders its matched child directly.

## When a slot has no match

For `/customers/segments`, `(inspector)` has no `segments` route. What renders in a route slot without a match:

1. **`default.py`**, if the slot has one. `(inspector)/default.py` renders, for example, "Pick a customer".
2. Otherwise, **the slot renders empty.** It gets an empty container, and whatever it showed before is removed. Nothing is kept from an earlier URL.

The URL itself is only "not found" when neither the main branch nor a route slot matches it.

In the showcase, `(pinned)` has no `insights` route and no `default.py`. Open a customer, then click **Insights**: the `insights` page renders in `children`, and `(pinned)` goes empty. A fresh load of `/customers/insights` behaves the same way.

Give a route slot a `default.py` if it should show something when its URL does not match. `RouteTester` reports these slots with mode `empty` ([Testing routes](testing.md)).

## Put a static prefix in front of `[param]` in slots

A `[param]` folder matches any single segment. Inside a route slot, a bare `(inspector)/[customer_id]/` would also match `/customers/segments` and `/customers/insights`, with `customer_id="segments"`. Put a fixed segment in front:

```text
(inspector)/accounts/[customer_id]/    matches /customers/accounts/3 only
```

URLs that do not start with `accounts/` then fall through to the slot's `default.py`.

## Do not name a slot like a query parameter

Slot arguments and query values share the layout's keyword arguments. A slot named `(status)` hides a `?status=` query value from that layout. Pick slot names that no layout reads from the query string.

## Slots in tests

```python
tester.assert_routes(
    old="/customers/accounts/3",
    new="/customers/segments",
    expected=["customers/segments", "customers/(inspector)", "customers/(pinned)/segments"],
    expected_modes={"customers/(inspector)": "default"},
)
```

Node ids of slot routes include the slot folder: `customers/(inspector)/accounts/[customer_id]`. `url_for` skips slot segments, so `url_for("customers/(inspector)/accounts/[customer_id]", customer_id=3)` returns `/customers/accounts/3`.
