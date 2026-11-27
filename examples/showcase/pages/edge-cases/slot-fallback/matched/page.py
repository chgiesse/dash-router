from edge_helpers import case_card, edge_badge

URL = "/edge-cases/slot-fallback/matched"


def page(**_):
    return case_card(
        "/edge-cases/slot-fallback/matched",
        edge_badge("slot-matched", URL),
        "Both slots matched this URL. Open /other to see the fallbacks.",
    )
