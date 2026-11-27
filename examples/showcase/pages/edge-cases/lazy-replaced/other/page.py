from edge_helpers import edge_badge, part_card


def page(**_):
    url = "/edge-cases/lazy-replaced/other"
    return part_card("Other", edge_badge("lazy-replaced-other", url), "Other replaced the slow lazy boundary.")
