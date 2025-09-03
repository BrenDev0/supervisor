from src.workflow.services.prompt_service import PromptService
from langchain_openai import ChatOpenAI
from src.workflow.state import State
from src.workflow.services.llm_service import LlmService
from src.utils.decorators.error_handler import error_handler
from src.workflow.agents.supervisor.supervisor_models import SupervisorOutput

class Supervisor:
    __MODULE = "context_orchestrator.agent"
    def __init__(self, prompt_service: PromptService, llm_service: LlmService):
        self.__prompt_service = prompt_service
        self.__llm_service = llm_service

    @error_handler(module=__MODULE)
    async def __get_prompt_template(self, state: State):
        system_message = """
        You are an expert workflow orchestrator for a company assistant platform.
        Given a user's query and their context, your job is to decide which specialized agents should be involved in answering the query.

        Available agents:
        - 95e222ef-c637-42d3-a81e-955beeeb0ba2: Handles questions about the law, legal system, statutes, or regulations.

        Only set an agent's UUID to true if their expertise is required for the query. 

        Examples:
        User query: "Can I terminate an employee without notice?"
        Output: {"95e222ef-c637-42d3-a81e-955beeeb0ba2": true}

        User query: "How do I reset my company email password?"
        Output: {"95e222ef-c637-42d3-a81e-955beeeb0ba2": false}
        """
        prompt = await self.__prompt_service.custom_prompt_template(state=state, system_message=system_message, with_chat_history=True)

        return prompt

    @error_handler(module=__MODULE)
    async def interact(self, state: State):
        llm = self.__llm_service.get_llm(temperature=0.1)
        
        prompt = await self.__get_prompt_template(state)
        
        structured_llm  = llm.with_structured_output(SupervisorOutput)
        chain = prompt | structured_llm
        
        response = await chain.ainvoke({"input": state["input"]})

        return response