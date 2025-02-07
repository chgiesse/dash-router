import dash_mantine_components as dmc
from dash import html

from router import RouteConfig
from router.components import ChildContainer

from ._components.figures import create_line_chart
from ._components.tabs import InvoiceTabs

config = RouteConfig(path_template="<invoice_id>", default_child="items")


# async def layout(children: ChildContainer, invoice_id: int = None, **kwargs):
def layout(children: ChildContainer, invoice_id: int = None, **kwargs):
    if not invoice_id:
        return html.Div("Select an invoice")

    return dmc.Stack(
        [
            dmc.Title("Invoice ID: " + str(invoice_id), order=2),
            create_line_chart(),
            InvoiceTabs(children.props.active, invoice_id),
            dmc.Divider(),
            html.Div(children),
        ]
    )
