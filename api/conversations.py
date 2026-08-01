from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session

from db import get_db_session
from deps import get_current_user_id, Role
from model import Conversations, Messages
from repositories.conversation_repo import db_get_all_conversations, db_create_conversation, db_get_conversation_by_id
from repositories.message_repo import db_get_all_messages_for_conversation, db_create_message
from repositories.persona_repo import db_get_persona
from schemas import ConversationOut, ConversationCreate, ConversationDetail

router = APIRouter(tags=["conversations"])


@router.get("/conversations", response_model=list[ConversationOut],
            summary="Get all conversations for the current user")
def get_conversations(user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db_session)):
    return db_get_all_conversations(user_id=user_id, db_session=db)  # Fetch all conversations for the user


@router.post("/conversations", response_model=ConversationOut,
             summary="Create a new conversation for the user with a persona")
def create_conversation(body: ConversationCreate,
                        user_id: UUID = Depends(get_current_user_id),
                        db: Session = Depends(get_db_session)):
    persona_in_db = db_get_persona(body.persona_key, db_session=db)  # Fetch all personas from the database
    if not persona_in_db:
        raise HTTPException(status_code=404,
                            detail="Persona not found, Please provide a valid persona key.")  # Raise an error if the persona does not exist
    # Create a new conversation for the user with the specified persona
    conversation = db_create_conversation(Conversations(user_id=user_id, persona_key=body.persona_key), db)
    db_create_message(
        message=Messages(
            conversation_id=conversation.id,
            role=Role.SYSTEM.value,
            content=next((persona.system_prompt for persona in persona_in_db if persona.key == body.persona_key), "")
        ),
        db_session=db
    )
    return conversation


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail,
            summary="Get all messages for a conversation")
def get_messages_for_conversation(user_id: UUID = Depends(get_current_user_id), conversation_id: UUID = None,
                                  db: Session = Depends(get_db_session)):
    conversation = db_get_conversation_by_id(user_id, conversation_id, db)  # Ensure the conversation exists
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db_get_all_messages_for_conversation(conversation_id, db)
    return ConversationDetail(
        id=conversation.id,
        persona_key=conversation.persona_key,
        title=conversation.title,
        updated_at=conversation.updated_at,
        messages=messages
    )
