from src.api.modules.websocket.websocket_service import WebsocketService
from src.utils.http.get_hmac_header import generate_hmac_headers
from src.workflow.state import State
from fastapi import WebSocket
from src.api.modules.interactions.interactions_models import WorkerState
import httpx
import os
import asyncio
from uuid import UUID

class Orchestrator:
    def __init__(self, websocket_service: WebsocketService):
        self.__websocket_service = websocket_service

    @staticmethod
    async def __handle_agent_interaction(agent_id: str, state: State, worker_state: WorkerState, websocket: WebSocket):
        hmac_secret = os.getenv("HMAC_SECRET")
        worker_host = os.getenv("WORKER_HOST")
        
        agent_endpoint = f"{agent_id}{worker_host}"
        worker_headers = generate_hmac_headers(hmac_secret)
        payload = worker_state.model_dump()  

        ## interacts with the worker agent
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{agent_endpoint}/interactions/internal/interact",
                headers=worker_headers,
                json=payload,
                timeout=30.0
            )
            agent_response = response.json()

        ## sends response to frontend
        await websocket.send_json({
            "agent_id": agent_id,
            "response": agent_response
        })

        ## saves messages and updates redis 
        main_server_endpoint = os.getenv("MAIN_SERVER_ENDPOINT")
        main_server_headers = generate_hmac_headers(hmac_secret)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://{main_server_endpoint}/interactions/internal/outgoing/{state["chat_id"]}",
                headers=main_server_headers,
                json={
                    "human_message": state["input"],
                    "agent_id": agent_id,
                    "ai_message": agent_response
                }
            )

    async def orchestrate(self, state: State, worker_state: WorkerState):
        websocket: WebSocket = self.__websocket_service.get_connection(state["chat_id"]) 

        
        selected_agent_ids = [
            str(agent_id)
            for agent_id, selected in state["selected_agents"].root.items()
            if selected and agent_id in state["available_agents"]
        ]

        ## send frontend list of agents responding
        await websocket.send_json({
            "agents": selected_agent_ids
        })

        ## send responses to front end
        await asyncio.gather(
            *(
                self.__handle_agent_interaction(
                    agent_id=agent_id,
                    state=state,
                    worker_state=worker_state,
                    websocket=websocket
                ) for agent_id in selected_agent_ids
            )
        )

        return state   

    