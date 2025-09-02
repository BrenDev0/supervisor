from fastapi import APIRouter, Request, Body, Depends
from  src.api.core.middleware.middleware_service import security
from src.api.core.middleware.auth_middleware import auth_middleware
from src.api.core.models.http_models import CommonHttpReponse
from uuid import UUID
from src.utils.http.get_hmac_header import generate_hmac_headers
import httpx
import os
from src.workflow.graph import create_graph
from src.api.modules.interactions.interactions_models import WorkerState, InteractionRequest

router = APIRouter(
    prefix="/interactions",
    dependencies=[Depends(security)],
    tags=["Interactions"]
)

def get_state_factory(chat_id: UUID):
    async def get_state(req: Request, data: InteractionRequest = Body(...), _: None = Depends(auth_middleware)):
        """
        get the payload to send to the agents servers
        """
        user_id = req.state.user
        company_id = req.state.company
        
        hmac_secret = os.getenv("HMAC_SECRET")
        headers = generate_hmac_headers(hmac_secret)

        main_server_endpoint = os.get("MAIN_SERVER_ENDPOINT")

        req_body = {
            "user_id": user_id,
            "company_id": company_id,
            "input": data.input
        }

        async with httpx.AsyncClient() as client:
            res = client.post(
                headers=headers,
                url=f"https://{main_server_endpoint}/interactions/internal/incoming/{chat_id}",
                json=req_body
            )

            res.raise_for_status()
            res_data = res.json()
            worker_state = WorkerState(**res_data)
            return worker_state
    
    return get_state

def get_graph(state: WorkerState = Depends(get_state_factory)):
    return create_graph(state=state)


@router.post("/secure/{chat_id}", status_code=202, response_model=CommonHttpReponse)
def secure_interact(
    chat_id: UUID,
    req: Request,
    data: InteractionRequest = Body(...), # added for docs
    worker_state: WorkerState = Depends(get_state_factory), # handles user auth
    graph = Depends(get_graph) 
):
    pass