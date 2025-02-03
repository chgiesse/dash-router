from dash import _dash_renderer
from flash import Flash

from appshell import create_appshell
from router import RootContainer, Router

# from pages.sales.page import layout


_dash_renderer._set_react_version("18.2.0")
app = Flash(__name__, suppress_callback_exceptions=True)

router = Router(app)

app.layout = create_appshell([RootContainer()])


if __name__ == "__main__":
    app.run(debug=True, port=8031)
