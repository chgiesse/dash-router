import dash_mantine_components as dmc


class InvoiceTabs(dmc.Tabs):
    class ids:
        tabs = "invoice-tabs"

    def __init__(self, active_tab: str = None, invoice_id: str = None):
        super().__init__(
            id=self.ids.tabs,
            variant="pills",
            color="dark",
            value=active_tab,
            children=dmc.TabsList(
                [
                    dmc.Anchor(
                        dmc.TabsTab("Items", value="items"),
                        href=f"/sales/invoices/{str(invoice_id)}/items",
                        underline=False,
                    ),
                    dmc.Anchor(
                        dmc.TabsTab("Positions", value="positions"),
                        href=f"/sales/invoices/{str(invoice_id)}/positions",
                        underline=False,
                    ),
                    # dmc.Anchor(dmc.TabsTab('Invoices', value='invoices'), href='/sales/invoices', underline=False),
                ]
            ),
        )
