from edge_helpers import edge_badge, part_card


def page(**_):
    url = "/edge-cases/slot-fallback/other"
    return part_card("Other", edge_badge("slot-other", url), "Neither slot has a route for /other.")
