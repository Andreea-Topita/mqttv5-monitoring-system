from pydantic import BaseModel


class ActionResponse(BaseModel):
    success: bool = True
    message: str