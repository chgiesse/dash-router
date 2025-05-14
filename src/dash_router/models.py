from typing import Dict, Literal
from pydantic import BaseModel


LoadingStateType = Literal["lacy", "done", "hidden"] | None


class RouterResponse(BaseModel):
    response: Dict[str, any]
    mimetype: str = "application/json"
    multi: bool = False

    class Config:
        arbitrary_types_allowed = True
