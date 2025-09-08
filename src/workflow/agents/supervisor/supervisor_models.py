from pydantic import BaseModel
from typing import Dict, List


class SupervisorOutput(BaseModel):
    selected_agents: List[str]