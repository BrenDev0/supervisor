from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from typing import List, Dict, Any
from src.workflow.state import State

class PromptService:
    async def custom_prompt_template(self, state: State, system_message: str, with_chat_history: bool = False):
        messages = [
            SystemMessage(content=system_message)
        ]

        if with_chat_history:
            messages = self.add_chat_history(state, messages)

        messages.append(HumanMessagePromptTemplate.from_template('{input}'))

        prompt = ChatPromptTemplate.from_messages(messages)

        return prompt


    @staticmethod
    def add_chat_history(state: State, messages: List[Any]) -> List[Any]:

        chat_history = state.get("chat_history", [])
        if chat_history:
            for msg in chat_history:
                if msg["type"] == "human":
                    messages.append(HumanMessage(content=msg["text"]))
                elif msg["type"] == "ai":
                    messages.append(AIMessage(content=msg["text"]))

        return messages
    
    
    
    