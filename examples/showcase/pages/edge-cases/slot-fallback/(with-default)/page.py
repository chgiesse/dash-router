from dash_router import ChildContainer
from edge_helpers import edge_badge, part_card


def page(children: ChildContainer, **_):
    url = "/edge-cases/slot-fallback (with-default)"
    return part_card("(with-default) slot", edge_badge("slot-with-default-layout", url), children)
