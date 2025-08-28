from pydantic import BaseModel, Field

class SupervisorOutput(BaseModel):
    legal: bool = Field(
        False, 
        description="True if the query requires information about the law, legal system, statutes, or regulations"
    )
   
 