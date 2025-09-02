import os
import httpx
from langchain_openai import ChatOpenAI
from typing import List
from src.workflow.state import State
from src.dependencies.container import Container
from langgraph.graph import StateGraph, END, START
from src.utils.http.get_hmac_header import generate_hmac_headers
from src.utils.decorators.error_handler import error_handler
from src.workflow.agents.supervisor.supervisor_agent import Supervisor
from src.api.modules.interactions.interactions_models import WorkerState

def create_graph(worker_state: WorkerState):
    graph = StateGraph(State)
    module = "graph"
    hmac_secret = os.getenv("HMAC_SECRET")

    async def supervisor(state: State):
        supervisor: Supervisor = Container.resolve("supervisor_agent")

        response = supervisor.interact(state=state)

        return {"selected_agents": response} 

    def router(state: State):
        pass


    @error_handler(module=module)
    async def legal_assistant(state: State): 
        headers = generate_hmac_headers(secret=hmac_secret)
        endpoint = os.getenv("LEGAL_ASSISTANT_ENDPOINT")
        payload = worker_state.model_dump()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{endpoint}/interactions/secure/interact",  
                json=payload,
                headers=headers,
                timeout=30.0
            )
        
        return response["final_reponse"]



        

    graph.add_node("supervisor", supervisor)
    graph.add_node("router", router)
    

    graph.add_edge(START, "supervisor")

    




    return graph.compile()