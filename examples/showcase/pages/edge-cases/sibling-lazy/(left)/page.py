from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/sibling-lazy (left)"
    return part_card("(left) · lazy", edge_badge("sibling-left", url), f"{data}: streamed in once, never restarted.")
