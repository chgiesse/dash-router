import dash_mantine_components as dmc

async def layout(**kwargs):
    return [
        dmc.Anchor(href='/sales/invoices/1', children='invoice id: 1'),
        dmc.Anchor(href='/sales/invoices/2', children='invoice id: 2'),
        dmc.Anchor(href='/sales/invoices/3', children='invoice id: 3'),
    ]