from fastapi import APIRouter, Request, Body, Depends, BackgroundTasks, Path
from  src.api.core.middleware.middleware_service import security
from src.api.core.middleware.auth_middleware import auth_middleware
from src.api.core.models.http_models import CommonHttpReponse
from uuid import UUID
from src.utils.http.get_hmac_header import generate_hmac_headers
import httpx
import os
from src.workflow.graph import create_graph
from src.api.modules.interactions.interactions_models import WorkerState, InteractionRequest
from src.dependencies.container import Container
from src.api.modules.interactions.interactions_controller import InteractionsController

router = APIRouter(
    prefix="/interactions",
    dependencies=[Depends(security)],
    tags=["Interactions"]
)


async def get_worker_state(
        req: Request,
        chat_id: UUID = Path(...), 
        data: InteractionRequest = Body(...), 
        _: None = Depends(auth_middleware)
):
    """
    get the payload to send to the agents servers
    """
    user_id = req.state.user
    company_id = req.state.company
    
    hmac_secret = os.getenv("HMAC_SECRET")

    headers = generate_hmac_headers(hmac_secret)

    main_server_endpoint = os.getenv("MAIN_SERVER_ENDPOINT")

    req_body = {
        "user_id": user_id,
        "company_id": company_id,
        "input": data.input
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            headers=headers,
            url=f"https://{main_server_endpoint}/interactions/internal/incomming/{chat_id}",
            json=req_body
        )

        res.raise_for_status()
        res_data = res.json()
        worker_state = WorkerState(**res_data)
        return worker_state

    return get_state

def get_graph(state: WorkerState = Depends(get_worker_state)):
    return create_graph(worker_state=state)

def get_controller():
    return InteractionsController()



@router.post("/secure/{chat_id}", status_code=202, response_model=CommonHttpReponse)
def secure_interact(
    background_tasks: BackgroundTasks,
    chat_id: UUID,
    req: Request,
    data: InteractionRequest = Body(...), # added for docs
    worker_state: WorkerState = Depends(get_worker_state), # handles user auth
    graph = Depends(get_graph),
    controller: InteractionsController = Depends(get_controller)
):
    """
    ## Interaction request

    Use this endpoint to interact with the agents.
    Only company marked tokens have access to this endpoint.
    """
    return controller.interact_request(
        background_tasks=background_tasks,
        worker_state=worker_state,
        graph=graph
    )