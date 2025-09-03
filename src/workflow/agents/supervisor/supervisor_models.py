from pydantic import RootModel
from typing import Dict
from uuid import UUID

class SupervisorOutput(RootModel[Dict[UUID, bool]]):
    pass