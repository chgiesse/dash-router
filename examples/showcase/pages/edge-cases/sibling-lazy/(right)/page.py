from edge_helpers import edge_badge, part_card


def page(tag: str = "a", **_):
    url = f"/edge-cases/sibling-lazy?tag={tag}"
    return part_card("(right) · tag", edge_badge("sibling-right", url), f"tag={tag}")
