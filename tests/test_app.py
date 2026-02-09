from dash import html
from flash import Flash
from flash_router import FlashRouter, RootContainer

# from utils.helpers import store_route_table, store_route_tree


app = Flash(
    __name__,
    prevent_initial_callbacks=True,
    pages_folder="pages",
    use_pages=False,
    router=FlashRouter,
)

app.layout = html.Div(RootContainer(), className="app-root")

# store_route_table()
# store_route_tree()

app.run(port=33333, debug=True)
