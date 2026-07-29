from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import personas, messages
from llm.agent import build_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the agent ONCE when the server boots, not on every request.
    app.state.agent = build_agent()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(personas.router)
app.include_router(messages.router)


@app.get("/health")
def read_health():
    return {"status": "ok"}
