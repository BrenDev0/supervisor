from dotenv import load_dotenv
load_dotenv()
import pytest
from uuid import uuid4, UUID
from src.workflow.graph import create_graph
from src.api.modules.interactions.interactions_models import WorkerState
from src.workflow.state import State
from src.dependencies.configure_container import configure_container

@pytest.mark.asyncio
async def test_graph_integration():

    configure_container()
    # Setup test data
    agent_id = "95e222ef-c637-42d3-a81e-955beeeb0ba2"
   
    worker_state = WorkerState(
        input="¿Cuál es la primera articulo del CONSTITUCIÓN POLÍTICA DE LOS ESTADOS UNIDOS MEXICANOS",
        agents=["95e222ef-c637-42d3-a81e-955beeeb0ba2"],
        chat_id="0e4c6ce5-0cae-436c-bbd1-62201a422ac6",
        company_id="218c9b2a-33d1-44c8-844a-5d302bc4a479",
        chat_history=[],
        user_id= "4a1f37dc-8bf3-4494-a002-9fbbb1445c9d"
    )

    # Initial state for the graph
    state: State = {
        "input": worker_state.input,
        "chat_id": worker_state.chat_id,
        "available_agents": worker_state.agents,
        "selected_agents": []  
    }

    # Run the graph
    graph = create_graph(worker_state)
    result = await graph.ainvoke(state)

    print("Final state:", result)
   
    assert "selected_agents" in result
    assert isinstance(result["selected_agents"], list)
    assert str(agent_id) in result["selected_agents"]