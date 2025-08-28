from langchain_openai import ChatOpenAI

class LlmService:
    @staticmethod
    def get_llm(
        temperature: float,
        max_tokens: int = None
    ):
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            max_completion_tokens=max_tokens
        )

        return llm