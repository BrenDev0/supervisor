from pydantic import BaseModel

class CommonHttpReponse(BaseModel):
    detail: str