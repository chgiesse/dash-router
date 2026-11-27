from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/lazy-race/next"
    return part_card("Next", edge_badge("lazy-race-next", url), f"{data}: landed.")
