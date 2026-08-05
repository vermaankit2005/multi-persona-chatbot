from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from api import personas, messages, conversations
from config import settings
from llm.agent import build_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the agent ONCE when the server boots, not on every request.
    app.state.agent = build_agent()
    yield


app = FastAPI(lifespan=lifespan)

# The frontend runs on a different origin, so the browser sends a preflight
# OPTIONS before every call. Without this middleware that preflight 405s and
# nothing reaches the routers below.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(personas.router)
app.include_router(messages.router)
app.include_router(conversations.router)


@app.get("/health")
def read_health():
    return {"status": "ok"}


@app.exception_handler(LookupError)
def handle_not_found(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})