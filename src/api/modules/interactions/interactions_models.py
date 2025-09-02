from pydantic import BaseModel
from uuid import UUID
from typing import List, Any, Dict

class InteractionRequest(BaseModel):
    input: str

class WorkerState(BaseModel):
    input: str
    chat_id: UUID
    company_id: UUID
    chat_history: List[Dict[str, Any]]
    user_id: UUID