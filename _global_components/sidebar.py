import dash_mantine_components as dmc
from dash.html import Div
from dash_iconify import DashIconify
from flash import Input, Output, clientside_callback

from helpers import get_icon

theme_toggle = dmc.Switch(
    mt="auto",
    offLabel=DashIconify(
        icon="radix-icons:sun", width=15, color=dmc.DEFAULT_THEME["colors"]["yellow"][8]
    ),
    onLabel=DashIconify(
        icon="radix-icons:moon",
        width=15,
        color=dmc.DEFAULT_THEME["colors"]["yellow"][6],
    ),
    id="color-scheme-toggle",
    persistence=True,
    color="grey",
)

clientside_callback(
    """ 
    (switchOn) => {
       document.documentElement.setAttribute('data-mantine-color-scheme', switchOn ? 'dark' : 'light');  
       return window.dash_clientside.no_update
    }
    """,
    Output("color-scheme-toggle", "id"),
    Input("color-scheme-toggle", "checked"),
)


def create_navlink(href: str, icon: str, *args, **kwargs):
    return dmc.Anchor(
        dmc.ActionIcon(get_icon(icon, height=25), size="xl", variant="subtle"),
        href=href,
        underline=False,
        *args,
        **kwargs,
    )


navbar = dmc.AppShellNavbar(
    dmc.Stack(
        align="center",
        gap="xs",
        mt="lg",
        children=[
            Div(get_icon("carbon:logo-python", height=35)),
            create_navlink(
                href="/",
                icon="majesticons:home-line",
            ),
            create_navlink(href="/sales", icon="icon-park-outline:sales-report"),
            create_navlink(href="/page-2", icon="majesticons:file-line", mt="auto"),
            dmc.Menu(
                [
                    dmc.MenuTarget(
                        dmc.ActionIcon(
                            get_icon(
                                "material-symbols:settings-outline-rounded", height=30
                            ),
                            size="lg",
                            radius="xl",
                            variant="subtle",
                        )
                    ),
                    dmc.MenuDropdown([dmc.Group(["Theme", theme_toggle], m="sm")]),
                ],
                trigger="hover",
                position="right",
            ),
        ],
    )
)
