"""In-memory demo data for the Northwind Ops showcase (deterministic, no database)."""

import asyncio
import random
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

_rng = random.Random(7)

TODAY = date(2026, 11, 25)


class OrderStatus(str, Enum):
    ALL = "all"
    OPEN = "open"
    SHIPPED = "shipped"
    DELAYED = "delayed"
    RETURNED = "returned"


@dataclass(frozen=True)
class Customer:
    id: int
    name: str
    city: str
    segment: str
    lifetime_value: int
    risk: int  # 0..100


@dataclass(frozen=True)
class Order:
    id: int
    customer_id: int
    placed: date
    status: OrderStatus
    total: float
    items: int


_NAMES = [
    "Alfreds Futterkiste", "Ana Trujillo", "Antonio Moreno", "Around the Horn", "Berglunds",
    "Blauer See", "Blondel père", "Bólido Comidas", "Bon app'", "Bottom-Dollar",
    "Cactus Comidas", "Centro comercial", "Chop-suey", "Comércio Mineiro", "Consolidated",
    "Drachenblut", "Du monde entier", "Eastern Connection", "Ernst Handel", "Familia Arquibaldo",
]
_CITIES = ["Berlin", "México D.F.", "London", "Luleå", "Mannheim", "Strasbourg", "Madrid", "Marseille"]
_SEGMENTS = ["Retail", "Wholesale", "Enterprise"]

CUSTOMERS: dict[int, Customer] = {
    i + 1: Customer(
        id=i + 1,
        name=name,
        city=_rng.choice(_CITIES),
        segment=_rng.choice(_SEGMENTS),
        lifetime_value=_rng.randint(4_000, 180_000),
        risk=_rng.randint(3, 92),
    )
    for i, name in enumerate(_NAMES)
}

_STATUS_WEIGHTS = [
    (OrderStatus.OPEN, 4),
    (OrderStatus.SHIPPED, 8),
    (OrderStatus.DELAYED, 2),
    (OrderStatus.RETURNED, 1),
]

ORDERS: dict[int, Order] = {}
for _i in range(64):
    _oid = 1001 + _i
    ORDERS[_oid] = Order(
        id=_oid,
        customer_id=_rng.randint(1, len(CUSTOMERS)),
        placed=TODAY - timedelta(days=_rng.randint(0, 120)),
        status=_rng.choices([s for s, _ in _STATUS_WEIGHTS], [w for _, w in _STATUS_WEIGHTS])[0],
        total=round(_rng.uniform(40, 4_800), 2),
        items=_rng.randint(1, 14),
    )

DOCS: dict[str, object] = {
    "getting-started": {
        "_title": "Getting started",
        "_body": "Northwind Ops is the back office for orders, customers and fulfilment.",
        "accounts": {"_title": "Accounts & roles", "_body": "Invite teammates and assign roles."},
        "first-order": {"_title": "Your first order", "_body": "Create an order from the Orders view."},
    },
    "fulfilment": {
        "_title": "Fulfilment",
        "_body": "Everything about picking, packing and shipping.",
        "shipping": {
            "_title": "Shipping",
            "_body": "Carrier rules, cut-off times and labels.",
            "returns": {"_title": "Returns", "_body": "Returns are accepted within 30 days."},
            "international": {"_title": "International", "_body": "Customs forms are generated automatically."},
        },
        "delays": {"_title": "Handling delays", "_body": "Delayed orders are flagged after 48h."},
    },
}


async def simulate_latency(seconds: float) -> None:
    """Pretend to talk to a database or an upstream API."""
    await asyncio.sleep(seconds)


def filter_orders(status: OrderStatus, q: str) -> list[Order]:
    rows = sorted(ORDERS.values(), key=lambda o: o.placed, reverse=True)
    if status is not OrderStatus.ALL:
        rows = [o for o in rows if o.status is status]
    if q:
        needle = q.lower()
        rows = [
            o for o in rows
            if needle in str(o.id) or needle in CUSTOMERS[o.customer_id].name.lower()
        ]
    return rows


def revenue_series(days: int) -> list[dict[str, object]]:
    rng = random.Random(days)
    out: list[dict[str, object]] = []
    for offset in range(days, 0, -max(1, days // 15)):
        day = TODAY - timedelta(days=offset)
        out.append(
            {
                "date": day.strftime("%b %d"),
                "Revenue": rng.randint(8_000, 26_000),
                "Refunds": rng.randint(200, 3_000),
            }
        )
    return out


def order_timeline(order: Order) -> list[tuple[str, str]]:
    steps = [("Order placed", order.placed.isoformat())]
    if order.status in (OrderStatus.SHIPPED, OrderStatus.RETURNED, OrderStatus.DELAYED):
        steps.append(("Picked & packed", (order.placed + timedelta(days=1)).isoformat()))
    if order.status in (OrderStatus.SHIPPED, OrderStatus.RETURNED):
        steps.append(("Shipped", (order.placed + timedelta(days=2)).isoformat()))
    if order.status is OrderStatus.DELAYED:
        steps.append(("Carrier delay reported", (order.placed + timedelta(days=4)).isoformat()))
    if order.status is OrderStatus.RETURNED:
        steps.append(("Return received", (order.placed + timedelta(days=9)).isoformat()))
    return steps


def resolve_doc(path: list[str]) -> tuple[list[tuple[str, str]], dict[str, object] | None]:
    """Walk `DOCS` along `path`; returns breadcrumbs and the page (or `None` if unknown)."""
    node: object = DOCS
    crumbs: list[tuple[str, str]] = []
    for depth, seg in enumerate(path):
        if not isinstance(node, dict) or seg not in node:
            return crumbs, None
        node = node[seg]
        title = node.get("_title", seg) if isinstance(node, dict) else seg
        crumbs.append((str(title), "/docs/" + "/".join(path[: depth + 1])))
    return crumbs, node if isinstance(node, dict) else None
