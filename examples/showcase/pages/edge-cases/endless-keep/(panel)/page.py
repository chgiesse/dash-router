from edge_helpers import edge_badge, part_card


def page(panel: str = "a", **_):
    url = f"/edge-cases/endless-keep?panel={panel}"
    return part_card("(panel) · ?panel=", edge_badge("endless-keep-panel", url), f"panel={panel}")
