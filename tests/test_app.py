from dash import html
from pathlib import Path
from flash import Flash
from flash_router import FlashRouter, RootContainer
from flash_router.core.routing import RouteRegistry

# from utils.helpers import store_route_table, store_route_tree


app = Flash(
    __name__,
    # prevent_initial_callbacks=True,
    # suppress_callback_exceptions=True,
    pages_folder=str(Path(__file__).parent / "pages"),
    use_pages=False,
    router=FlashRouter,
)

app.layout = html.Div(RootContainer(), className="app-root")

# store_route_table()
# store_route_tree()
print(RouteRegistry._dynamic_root)
print(RouteRegistry._nodes.get("projects/[team-id]"))

app.run(port=33333, debug=True)
