from edge_helpers import edge_badge, part_card


def page(data: str, **_):
    url = "/edge-cases/history/three"
    return part_card("History · three", edge_badge("history-three", url), f"api.py {data} landed after 0.6 s")
