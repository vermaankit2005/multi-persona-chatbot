from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from llm.provider import groq_llm

search_tool = TavilySearch(
    max_results=2,
    topic="news",
    include_images=False,
    search_depth="advanced"
)

@tool("tavily_search")
def search_tool_func(query: str) -> str:
    """Wrapper function for the TavilySearch tool."""
    return search_tool.invoke({"query": query})


def build_agent():
    return create_agent(
        model=groq_llm(),
        tools=[search_tool_func],
        middleware=[
            ModelCallLimitMiddleware(run_limit=5, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=3, exit_behavior="continue"),
            PIIMiddleware("credit_card", strategy="mask", apply_to_output=True, apply_to_tool_results=True),
        ],
    )
