import dash_mantine_components as dmc

from ui import link, section


def page(name: str = "", **_):
    return section(
        "Saved",
        dmc.Stack(
            [
                dmc.Alert(f"Profile of {name or 'unknown'} saved.", color="teal", variant="light"),
                dmc.Text(
                    "This page was reached with navigate() from the save callback. The Transition log "
                    "shows it as a normal navigation.",
                    size="sm",
                    c="dimmed",
                ),
                link("Edit profile again", "/settings/profile", size="sm"),
            ]
        ),
        features=("query param `name`",),
    )
