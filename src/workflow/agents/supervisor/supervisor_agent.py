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
        - 99b5792d-c38a-4e49-9207-a3fa547905ae: Accounting & Data Analysis Agent - Handles:
          * General accounting principles and best practices
          * Financial data organization and management
          * Questions about company-specific financial data and spreadsheets
          * Data visualization requests for company financial information
          * Analysis of company financial metrics and reports
          * Questions involving numbers, costs, or financial calculations

        Only include an agent's UUID in the list if their expertise is required for the query.
        For the Accounting & Data Analysis Agent, include it when:
        1. The query mentions accounting concepts, financial terms, or business finances
        2. The user asks about specific company data, numbers, or reports
        3. The query involves analyzing, visualizing, or understanding financial information
        4. The user wants to perform calculations or comparisons with company data

        Examples:
        User query: "Can I terminate an employee without notice?"
        Output: {"selected_agents": ["95e222ef-c637-42d3-a81e-955beeeb0ba2"]}

        User query: "What's the best way to organize our expense categories?"
        Output: {"selected_agents": ["99b5792d-c38a-4e49-9207-a3fa547905ae"]}

        User query: "Show me our revenue trends for the last quarter"
        Output: {"selected_agents": ["99b5792d-c38a-4e49-9207-a3fa547905ae"]}

        User query: "How do I reset my company email password?"
        Output: {"selected_agents": []}

        User query: "Calculate our profit margins and compare them to industry standards"
        Output: {"selected_agents": ["99b5792d-c38a-4e49-9207-a3fa547905ae"]}
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