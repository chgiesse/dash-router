from pydantic import BaseModel, Field

from data import OrderStatus

PAGE_SIZE = 10


class OrderFilters(BaseModel):
    """Query string of the order list, parsed and validated by the router.

    `?status=delayed&q=berg&page=2` -> `OrderFilters(status=OrderStatus.DELAYED, q="berg", page=2)`.
    Omitted fields compare equal to their defaults, so `?page=1` does not re-render anything.
    """

    status: OrderStatus = OrderStatus.ALL
    q: str = ""
    page: int = Field(default=1, ge=1)

    def query(self, **overrides: object) -> str:
        values = {**self.model_dump(mode="json"), **overrides}
        defaults = OrderFilters().model_dump(mode="json")
        parts = [f"{k}={v}" for k, v in values.items() if v != defaults[k] and v not in ("", None)]
        return "?" + "&".join(parts) if parts else ""
