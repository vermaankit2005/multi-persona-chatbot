from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.responses import JSONResponse

from api import personas, messages, conversations
from llm.agent import build_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the agent ONCE when the server boots, not on every request.
    app.state.agent = build_agent()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(personas.router)
app.include_router(messages.router)
app.include_router(conversations.router)


@app.get("/health")
def read_health():
    return {"status": "ok"}


@app.exception_handler(LookupError)
def handle_not_found(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})