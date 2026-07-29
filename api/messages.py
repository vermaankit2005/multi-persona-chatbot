from fastapi import Body, Depends, APIRouter
from fastapi import Request
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.orm import Session

from db import get_db_session
from repositories.persona_repo import get_persona

router = APIRouter(tags=["messages"])

chat_history = {}  # Dictionary to store chat history for each chat_id


@router.post("/chat", response_model=str)
async def chat(request: Request,
               question: str = Body(..., description="User's question to the assistant"),
               chat_id: str = Body(..., description="Unique chat session ID"),
               persona: str = Body(..., description="Persona to use for the chat"),
               db: Session = Depends(get_db_session),
               ):
    agent = request.app.state.agent  # Access the agent from the app state

    if chat_id not in chat_history:
        chat_history[chat_id] = [
            SystemMessage(content=get_persona(db,
                                              persona).system_prompt)]  # Initialize chat history with system message for the persona

    chat_history[chat_id].append(HumanMessage(content=question))

    response = await agent.ainvoke({"messages": chat_history[chat_id]})
    chat_history[chat_id].append(response["messages"][-1])
    return response["messages"][-1].content
