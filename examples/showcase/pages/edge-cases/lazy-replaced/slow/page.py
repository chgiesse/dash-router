from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/lazy-replaced/slow"
    return part_card("Slow · landed", edge_badge("lazy-replaced-slow", url), f"{data}: this must never appear.")
