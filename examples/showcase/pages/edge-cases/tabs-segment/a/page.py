"""Default tab (`default_child="a"`): renders at `/edge-cases/tabs-segment` (or `/edge-cases/tabs-segment/a`)."""

from edge_helpers import edge_badge, part_card

URL = "/edge-cases/tabs-segment"


def page(**_):
    return part_card("Tab A (default)", edge_badge("tabs-segment-a", URL), "The default tab renders at the bare URL.")
