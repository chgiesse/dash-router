from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/lazy-race (lazy)"
    return part_card("(lazy) slot", edge_badge("lazy-race-lazy", url), f"{data}: landed.")
