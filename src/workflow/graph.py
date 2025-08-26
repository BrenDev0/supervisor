from langchain_openai import ChatOpenAI
from typing import List
from src.workflow.state import State
from src.dependencies.container import Container
from langgraph.graph import StateGraph, END, START

def create_graph():
    graph = StateGraph(State)

    async def supervisor(state: State):
        pass

    def router(state: State):
        pass

    async def legal_assistant(state: State): 
        pass
    
    async def responder(state: State):
        pass
        

    graph.add_node("supervisor", supervisor)
    graph.add_node("legal_assistant", legal_assistant)

    graph.add_edge(START, "supervisor")


    return graph.compile()