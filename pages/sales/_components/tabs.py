import dash_mantine_components as dmc 


class SalesTabs(dmc.Tabs):

    class ids:
        tabs = 'sales-tabs'


    def __init__(self, active_tab: str = None):
        super().__init__(
            id=self.ids.tabs,
            variant='pills',
            color='dark',
            value=active_tab,
            children=dmc.TabsList([
                dmc.Anchor(dmc.TabsTab('Overview', value='overview') , href='/sales/overview', underline=False),
                dmc.Anchor(dmc.TabsTab('Invoices', value='invoices') , href='/sales/invoices', underline=False),
                dmc.Anchor(dmc.TabsTab('Analytics', value='analytics') , href='/sales/analytics', underline=False),
                # dmc.Anchor(dmc.TabsTab('Invoices', value='invoices'), href='/sales/invoices', underline=False),
            ])
        )