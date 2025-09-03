from src.api.modules.interactions.interactions_models import WorkerState
from fastapi import BackgroundTasks
from src.api.core.models.http_models import CommonHttpReponse
from src.workflow.state import State

class InteractionsController:
    def interact_request(
        self,
        background_tasks: BackgroundTasks,
        worker_state: WorkerState,
        graph
    ) -> CommonHttpReponse:
        state = State(
            chat_id=worker_state.chat_id,
            input=worker_state.input,
            available_agents=worker_state.agents,
            selected_agents=""
        )
        
        background_tasks.add_task(graph.ainvoke, state)

        return CommonHttpReponse(
            detail="Request received"
        )


