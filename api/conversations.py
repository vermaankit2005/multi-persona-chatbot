from uuid import UUID

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from db import get_db_session
from deps import get_current_user_id
from repository.conversation_repo import db_get_all_conversations
from schemas import ConversationOut, ConversationCreate, ConversationDetail
from service import conversation_service

router = APIRouter(tags=["conversations"])


@router.get("/conversations", response_model=list[ConversationOut],
            summary="Get all conversations for the current user")
def get_conversations(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db_session)) -> list[ConversationOut]:
    return db_get_all_conversations(user_id=user_id, db_session=db)


@router.post("/conversations", response_model=ConversationOut,
             summary="Create a new conversation for the user with a persona")
def create_conversation(body: ConversationCreate,
                        user_id: UUID = Depends(get_current_user_id),
                        db: Session = Depends(get_db_session)) -> ConversationOut:
    return conversation_service.create_conversation(user_id, body.persona_key, db)  # Create a new conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail,
            summary="Get all messages for a conversation")
def get_messages_for_conversation(user_id: UUID = Depends(get_current_user_id),
                                  conversation_id: UUID = None,
                                  db: Session = Depends(get_db_session)) -> ConversationDetail:
    (conversation, messages) = conversation_service.get_messages_for_conversation(user_id, conversation_id, db)

    return ConversationDetail(
        id=conversation.id,
        persona_key=conversation.persona_key,
        title=conversation.title,
        updated_at=conversation.updated_at,
        messages=messages
    )
