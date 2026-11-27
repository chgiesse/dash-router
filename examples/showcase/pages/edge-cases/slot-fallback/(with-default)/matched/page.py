from edge_helpers import edge_badge, part_card


def page(**_):
    url = "/edge-cases/slot-fallback/matched (with-default)"
    return part_card("(with-default) · matched", edge_badge("slot-with-default-matched", url), "Matched.")
