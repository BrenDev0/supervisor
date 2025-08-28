from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from typing import List, Dict, Any
from src.workflow.services.embeddings_service import EmbeddingService
from src.workflow.state import State
from  datetime import datetime
class PromptService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service


    async def custom_prompt_template(self, state: State, system_message: str, with_chat_history: bool = False, with_context: bool = False, context_collection: str = None):
        messages = [
            SystemMessage(content=system_message)
        ]

        if with_chat_history:
            messages = self.add_chat_history(state, messages)

        if with_context & context_collection != None:
            messages = await self.add_context(input=state["input"], messages=messages, collection_name=context_collection)

        messages.append(HumanMessagePromptTemplate.from_template('{input}'))

        prompt = ChatPromptTemplate.from_messages(messages)

        return prompt


    async def add_context(self, input: str, messages: List[Dict[str, Any]], collection_name: str) -> List[Any]:
        context = await self.embedding_service.search_for_context(
            query=input,
            collection_name=collection_name
        )
 
        if context:
            messages.append(SystemMessage(content=f"""
                You have access to the following relevant context retrieved from documents.
                Use this information to inform your response. Do not make up facts outside of this context.

                Relevant context:
                {context}
            """))

        return messages

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
    
    
    
    