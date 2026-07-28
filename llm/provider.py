from langchain_groq import ChatGroq

from config import settings

def groq_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=settings.GROQ_API_KEY,
        temperature=0.7,
    )