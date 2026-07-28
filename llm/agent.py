from langchain.agents import create_agent

from llm.provider import groq_llm


def build_agent():
    return create_agent(
        model=groq_llm()
    )
