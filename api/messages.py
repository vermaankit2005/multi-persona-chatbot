from uuid import UUID

from fastapi import Body, Depends, APIRouter, HTTPException
from fastapi import Request
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from sqlalchemy.orm import Session

from db import get_db_session
from deps import Role
from model import Messages
from repositories.conversation_repo import db_get_conversation_by_id
from repositories.message_repo import db_create_message, db_get_recent_messages_for_conversation
from schemas import MessageTurnOut, MessageCreate, MessageOut

router = APIRouter(tags=["messages"])


@router.post("/conversations/{conversation_id}/messages", response_model=MessageTurnOut,
             summary="Send a message, get a reply")
def send_message(request: Request, messageContent: MessageCreate = Body(..., description="The content of the message"),
                 conversation_id: UUID = None, db: Session = Depends(get_db_session)):
    if conversation_id is None:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    conversation = db_get_conversation_by_id(conversation_id, db)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found for the given ID")

    # 1. Add the latest human message to the database
    message = Messages(
        conversation_id=conversation_id,
        role=Role.USER.value,
        content=messageContent.content
    )

    # 2. Get the recent messages for the conversation to provide context to the agent
    message_for_agent = db_get_recent_messages_for_conversation(conversation_id, db)

    # 3. Store the latest human message in the database
    latest_human_message = db_create_message(message, db)

    # 4. Convert messages to langchain format (SystemMessage for the persona already added during conversation creation)
    langchain_messages = []

    for msg in message_for_agent:
        if msg.role == Role.USER.value:
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == Role.ASSISTANT.value:
            langchain_messages.append(AIMessage(content=msg.content))
        elif msg.role == Role.SYSTEM.value:
            langchain_messages.append(SystemMessage(content=msg.content))

    # 5. Add the latest human message to the langchain messages
    langchain_messages.append(HumanMessage(content=latest_human_message.content))

    agent = request.app.state.agent

    # 6. Invoke the agent with the messages and get the assistant's response
    assistant_response = agent.invoke({"messages": langchain_messages})

    latest_assistant_message = db_create_message(Messages(
        conversation_id=conversation_id,
        role=Role.ASSISTANT.value,
        content=assistant_response["messages"][-1].content
        # Assuming the last message in the response is the assistant's reply
    ), db)

    # 7. Return both the latest human message and the assistant's response
    return MessageTurnOut(
        user_message=MessageOut.model_validate(latest_human_message, from_attributes=True),
        assistant_message=MessageOut.model_validate(latest_assistant_message, from_attributes=True)
    )
