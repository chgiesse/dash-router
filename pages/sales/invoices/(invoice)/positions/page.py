from dash import html


async def layout(**kwargs):
    return html.Div(f"All positions for invoice id: {kwargs.get('invoice_id')}")
