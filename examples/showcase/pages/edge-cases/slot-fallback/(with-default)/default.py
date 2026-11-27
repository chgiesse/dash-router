from edge_helpers import edge_badge, part_card


def default(**_):
    url = "/edge-cases/slot-fallback (with-default)"
    return part_card("(with-default) · default.py", edge_badge("slot-with-default-default", url), "Rendered because no route matched.")
