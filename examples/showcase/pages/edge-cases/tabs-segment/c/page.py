from edge_helpers import edge_badge, part_card

URL = "/edge-cases/tabs-segment/c"


def page(**_):
    return part_card("Tab C", edge_badge("tabs-segment-c", URL), 'Selected by the URL segment "c".')
