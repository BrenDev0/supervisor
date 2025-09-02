import os
import httpx
import asyncio
from src.workflow.state import State
from src.dependencies.container import Container
from langgraph.graph import StateGraph, END, START
from src.utils.http.get_hmac_header import generate_hmac_headers
from src.utils.decorators.error_handler import error_handler
from src.workflow.agents.supervisor.supervisor_agent import Supervisor
from src.api.modules.interactions.interactions_models import WorkerState
from src.api.modules.websocket.websocket_service import WebsocketService
from fastapi import WebSocket

def create_graph(worker_state: WorkerState):
    graph = StateGraph(State)
    module = "graph"
    AGENT_MAP = {
        "legal": "",
        "financial": ""
    }

    async def supervisor(state: State):
        supervisor: Supervisor = Container.resolve("supervisor_agent")

        response = supervisor.interact(state=state)

        return {"selected_agents": response} 


    @error_handler(module=module)
    async def router(state: State):
        websocket_service: WebsocketService = Container.resolve("websocket_service")
        websocket: WebSocket = websocket_service.get_connection(state["chat_id"]) 

        
        selected_agent_ids = []

        ## send frontend list of agents responding
        websocket.send_json({
            "agents": selected_agent_ids
        })

        async def handle_agent(agent_id):
            agent_endpoint = ""
            payload = worker_state.model_dump()  

            ## interacts with the agent
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{agent_endpoint}/interactions/internal/interact",
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
            hmac_secret = os.getenv("HMAC_SECRET")
            main_server_endpoint = os.getenv("MAIN_SERVER_ENDPOINT")
            headers = generate_hmac_headers(hmac_secret)
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://{main_server_endpoint}/interactions/internal/outgoing/{state["chat_id"]}",
                    headers=headers,
                    json={
                        "human_message": state["input"],
                        "agent_id": agent_id,
                        "ai_message": agent_response
                    }
                )

        await asyncio.gather(*(handle_agent(agent_id) for agent_id in selected_agent_ids))

        return state        

    graph.add_node("supervisor", supervisor)
    graph.add_node("router", router)
    

    graph.add_edge(START, "supervisor")
    graph.add_edge("router", END)

    
    return graph.compile()