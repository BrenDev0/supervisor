from typing_extensions import TypedDict
from typing import List, Dict
from uuid import UUID
from src.workflow.agents.supervisor.supervisor_models import SupervisorOutput

class State(TypedDict):
    input: str
    available_agents: List[UUID]       
    selected_agents: SupervisorOutput          