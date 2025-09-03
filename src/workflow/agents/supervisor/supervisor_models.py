from pydantic import BaseModel
from typing import Dict
from uuid import UUID

class SupervisorOutput(BaseModel):
    __root__: Dict[UUID, bool]
   
 