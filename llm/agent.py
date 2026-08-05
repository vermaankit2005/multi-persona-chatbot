from langchain.agents import create_agent
from langchain_tavily import TavilySearch

from llm.provider import groq_llm

search_tool = TavilySearch(
    max_results=1,
    topic="general",
    include_images=False,
    search_depth="basic"
)

def build_agent():
    return create_agent(
        model=groq_llm(),
        tools=[search_tool]
    )
