from fastapi import APIRouter, Request, Body, Depends
from  src.api.core.middleware.middleware_service import security
from src.api.core.middleware.auth_middleware import auth_middleware
from src.api.core.models.http_models import CommonHttpReponse
from uuid import UUID

router = APIRouter(
    prefix="/interactions",
    dependencies=[Depends(security)]
)

@router.post("/secure/{chat_id}", status_code=202, response_model=CommonHttpReponse)
def secure_interact(
    chat_id: UUID,
    req: Request,
    _: None = Depends(auth_middleware)
):
    pass