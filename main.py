from contextlib import asynccontextmanager

from fastapi import FastAPI, Body
from langchain_core.messages import HumanMessage

from llm.agent import build_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the agent ONCE when the server boots, not on every request.
    app.state.agent = build_agent()
    yield


app = FastAPI(lifespan=lifespan)

chat_history = {}  # Dictionary to store chat history for each chat_id


@app.get("/health")
def read_health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(question: str = Body(..., description="User's question to the assistant"),
               chat_id: str = Body(..., description="Unique chat session ID")):
    agent = app.state.agent

    if chat_id not in chat_history:
        chat_history[chat_id] = []

    chat_history[chat_id].append(HumanMessage(content=question))

    response = await agent.ainvoke({"messages": chat_history[chat_id]})
    chat_history[chat_id].append(response["messages"][-1])
    return response["messages"][-1].content
