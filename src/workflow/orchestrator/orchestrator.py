from src.api.modules.websocket.websocket_service import WebsocketService
from src.utils.http.get_hmac_header import generate_hmac_headers
from src.workflow.state import State
from fastapi import WebSocket, WebSocketDisconnect
from src.api.modules.interactions.interactions_models import WorkerState
import httpx
import os
import asyncio
from uuid import UUID

class Orchestrator:
    def __init__(self, websocket_service: WebsocketService):
        self.__websocket_service = websocket_service

    
    async def __handle_agent_interaction(self, agent_id: str, state: State, worker_state: WorkerState, websocket: WebSocket):
        hmac_secret = os.getenv("HMAC_SECRET")
        worker_host = os.getenv("WORKER_HOST")
        
        agent_endpoint = f"{agent_id}{worker_host}"
        worker_headers = generate_hmac_headers(hmac_secret)
        payload = worker_state.model_dump(mode="json")  

        ## interacts with the worker agent
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{agent_endpoint}/interactions/internal/interact",
                headers=worker_headers,
                json=payload,
                timeout=30.0
            )
            agent_response = response.json()
            final_response = agent_response.get("response", None)

        ## sends response to frontend
        if websocket is not None:
            try:
                await websocket.send_json({
                    "agent_id": agent_id,
                    "response": final_response
                })
            except (WebSocketDisconnect, RuntimeError):
                pass
    
        
        # only save message if response present
        if final_response:
            await self.__save_message(
                secret=hmac_secret,
                chat_id=state["chat_id"],
                sender=agent_id,
                message_type="ai",
                text=final_response
            )

    async def orchestrate(self, state: State, worker_state: WorkerState):
        websocket: WebSocket = self.__websocket_service.get_connection(state["chat_id"]) 

        await self.__save_message(
            secret=os.getenv("HMAC_SECRET"),
            chat_id=state["chat_id"],
            sender=worker_state.user_id,
            message_type="human",
            text=state["input"]
        )
        
        available_agent_ids = set(str(a) for a in state["available_agents"])
        selected_agent_ids = [
            agent_id
            for agent_id in state["selected_agents"]
            if agent_id in available_agent_ids
        ]

        ## send frontend list of agents responding
        if websocket is not None:
            try:
                await websocket.send_json({
                    "agents": selected_agent_ids
                })
            except (WebSocketDisconnect, RuntimeError):
                pass
        

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
    
    @staticmethod
    async def __save_message(secret: str, chat_id: UUID, sender: UUID, message_type: str, text: str):
        main_server_endpoint = os.getenv("MAIN_SERVER_ENDPOINT")
        main_server_headers = generate_hmac_headers(secret)
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://{main_server_endpoint}/messages/internal/{chat_id}",
                headers=main_server_headers,
                json={
                    "sender": str(sender),
                    "message_type": message_type,
                    "text": text
                }
            )

    