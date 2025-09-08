from src.workflow.state import State
from src.dependencies.container import Container
from langgraph.graph import StateGraph, END, START
from src.workflow.agents.supervisor.supervisor_agent import Supervisor
from src.api.modules.interactions.interactions_models import WorkerState
from src.workflow.orchestrator.orchestrator import Orchestrator

def create_graph(worker_state: WorkerState):
    graph = StateGraph(State)
 
    async def supervisor(state: State):
        supervisor: Supervisor = Container.resolve("supervisor")

        response = await supervisor.interact(state=state)
        print(response, "selcted agents::::::")

        return {"selected_agents": response.selected_agents}


    async def orchestrator(state: State):
        orchestrator: Orchestrator = Container.resolve("orchestrator")

        await orchestrator.orchestrate(state=state, worker_state=worker_state)

        return state        

    graph.add_node("supervisor", supervisor)
    graph.add_node("orchestrator", orchestrator)
    

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "orchestrator")
    graph.add_edge("orchestrator", END)

    
    return graph.compile()