from edge_helpers import edge_badge, part_card


def page(**_):
    url = "/edge-cases/slot-fallback/matched (no-default)"
    return part_card("(no-default) · matched", edge_badge("slot-no-default-matched", url), "Matched.")
