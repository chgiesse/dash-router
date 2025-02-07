import dash_mantine_components as dmc


def create_a_button(href: str):
    return dmc.Anchor(
        children=dmc.Button(
            "Open", variant="light", size="compact-sm"
        ).to_plotly_json(),
        underline=False,
        href=href,
    ).to_plotly_json()


def create_invoice_table():
    elements = [
        {
            "invoice_id": 1,
            "mass": "Amazon",
            "symbol": "2025-01-01",
            "action": "/sales/invoices/1",
        },
        {
            "invoice_id": 2,
            "mass": "Apple",
            "symbol": "2025-01-01",
            "action": "/sales/invoices/2",
        },
        {
            "invoice_id": 3,
            "mass": "Nvidia",
            "symbol": "2025-01-01",
            "action": "/sales/invoices/3",
        },
        {
            "invoice_id": 4,
            "mass": "AMD",
            "symbol": "2025-01-01",
            "action": "/sales/invoices/4",
        },
        {
            "invoice_id": 5,
            "mass": "Microsoft",
            "symbol": "2025-01-01",
            "action": "/sales/invoices/5",
        },
    ]

    rows = [
        dmc.TableTr(
            [
                dmc.TableTd(element["invoice_id"]),
                dmc.TableTd(element["mass"]),
                dmc.TableTd(element["symbol"]),
                dmc.TableTd(create_a_button(element["action"])),
            ]
        )
        for element in elements
    ]

    head = dmc.TableThead(
        dmc.TableTr(
            [
                dmc.TableTh("Invoice ID"),
                dmc.TableTh("Vendor"),
                dmc.TableTh("Issued Date"),
                dmc.TableTh("Action"),
            ]
        )
    )
    body = dmc.TableTbody(rows)

    return dmc.Table(
        [head, body],
        verticalSpacing="sm",
        horizontalSpacing="sm",
        highlightOnHover=True,
        withTableBorder=False,
        withColumnBorders=False,
        withRowBorders=False,
    )
