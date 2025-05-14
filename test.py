from flash import Flash
from src.dash_router.router import Router


app = Flash(__name__, pages_folder="flash_pages")
router = Router(app)
