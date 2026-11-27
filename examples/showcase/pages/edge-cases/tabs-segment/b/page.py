from edge_helpers import edge_badge, part_card

URL = "/edge-cases/tabs-segment/b"


def page(**_):
    return part_card("Tab B", edge_badge("tabs-segment-b", URL), 'Selected by the URL segment "b".')
