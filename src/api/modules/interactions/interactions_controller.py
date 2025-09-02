from src.api.modules.interactions.interactions_models import WorkerState
from fastapi import BackgroundTasks
from src.api.core.models.http_models import CommonHttpReponse

class InteractionsController:
    def interact_request(
        self,
        background_tasks: BackgroundTasks,
        worker_state: WorkerState,
        graph
    ) -> CommonHttpReponse:
        background_tasks.add_task(graph.ainvoke)

        return CommonHttpReponse(
            detail="Request received"
        )


