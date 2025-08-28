from typing_extensions import TypedDict
from typing import List, Dict

class State(TypedDict):
    input: str
    available_agents: List[str]       
    selected_agents: List[str]         
    agent_responses: Dict[str, str]     