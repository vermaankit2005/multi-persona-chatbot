from uuid import UUID

from fastapi import Body, Depends, APIRouter, HTTPException
from fastapi import Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from db import get_db_session
from deps import get_current_user_id
from repository.conversation_repo import db_get_conversation_by_id
from schemas import MessageTurnOut, MessageCreate, MessageOut
from service import chat_service, chat_service_stream

router = APIRouter(tags=["messages"])


@router.post("/conversations/{conversation_id}/messages", response_model=MessageTurnOut,
             summary="Send a message, get a reply")
def send_message(user_id: UUID = Depends(get_current_user_id),
                 request: Request = None,
                 message_content: MessageCreate = Body(..., description="The content of the message"),
                 conversation_id: UUID = None,
                 db: Session = Depends(get_db_session)) -> MessageTurnOut:
    if conversation_id is None:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    (latest_human_message, latest_assistant_message) = (
        chat_service.send_message(user_id, request.app.state.agent, message_content.content, conversation_id, db))

    return MessageTurnOut(
        user_message=MessageOut.model_validate(latest_human_message, from_attributes=True),
        assistant_message=MessageOut.model_validate(latest_assistant_message, from_attributes=True)
    )


@router.post("/conversations/{conversation_id}/messages/stream", response_class=StreamingResponse,
             summary="Send a message, get a reply (streaming)")
def send_message_stream(user_id: UUID = Depends(get_current_user_id),
                        request: Request = None,
                        message_content: MessageCreate = Body(..., description="The content of the message"),
                        conversation_id: UUID = None,
                        db: Session = Depends(get_db_session)) -> StreamingResponse:
    if conversation_id is None:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    # api/messages.py — option A: explicit guard in the route
    conversation = db_get_conversation_by_id(user_id, conversation_id, db)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return StreamingResponse(
        chat_service_stream.send_message_stream(user_id,
                                                request.app.state.agent,
                                                message_content.content,
                                                conversation_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # stops nginx buffering
        },
    )
