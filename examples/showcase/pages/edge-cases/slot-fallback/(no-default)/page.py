from dash_router import ChildContainer
from edge_helpers import edge_badge, part_card


def page(children: ChildContainer, **_):
    url = "/edge-cases/slot-fallback (no-default)"
    return part_card("(no-default) slot", edge_badge("slot-no-default-layout", url), children)
