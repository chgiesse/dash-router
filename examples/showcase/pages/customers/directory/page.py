import dash_mantine_components as dmc

from dash_router import url_for
from data import CUSTOMERS
from ui import link, money, section


def page(**_):
    rows = [
        dmc.TableTr(
            [
                dmc.TableTd(link(c.name, url_for("customers/accounts/[customer_id]", customer_id=c.id))),
                dmc.TableTd(c.city),
                dmc.TableTd(c.segment),
                dmc.TableTd(money(c.lifetime_value), ta="right"),
            ]
        )
        for c in CUSTOMERS.values()
    ]
    return section(
        "Directory",
        dmc.ScrollArea(
            dmc.Table(
                [
                    dmc.TableThead(dmc.TableTr([dmc.TableTh(h) for h in ("Customer", "City", "Segment", "Lifetime value")])),
                    dmc.TableTbody(rows),
                ],
                highlightOnHover=True,
                verticalSpacing=6,
            ),
            h=520,
        ),
        features=("default_child of /customers",),
    )
