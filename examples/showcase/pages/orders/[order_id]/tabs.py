"""The order tab bar, built by `page.py`. `UrlSegment` sets its value from the URL, so `active` is optional."""

import dash_mantine_components as dmc

ORDER_TABS = (("Summary", "summary"), ("Timeline", "timeline"), ("Notes", "notes"))
TABS_ID = "order-tabs"


def order_tabs(active: str | None = None) -> dmc.Tabs:
    return dmc.Tabs(
        dmc.TabsList([dmc.TabsTab(label, value=value) for label, value in ORDER_TABS]),
        id=TABS_ID,
        value=active,
    )
