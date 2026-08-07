from sqlalchemy import func

from model import Conversations

# List of conversation to show on left side of the UI, sorted by updated_at in descending order
def db_get_all_conversations(user_id, db_session) -> list[Conversations]:
    conversation = (db_session.query(Conversations)
            .filter(Conversations.user_id == user_id)
            .order_by(Conversations.updated_at.desc())
            .all())
    return conversation

def db_get_conversation_by_id(user_id, conversation_id, db_session) -> Conversations:
    conversation = db_session.query(Conversations).filter(Conversations.user_id == user_id, Conversations.id == conversation_id).first()
    return conversation

# Create a new conversation for the user with the specified persona
def db_create_conversation(conversation: Conversations, db_session) -> Conversations:
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation

def db_update_conversation_title(user_id, title: str, conversation_id, db_session) -> Conversations:
    conversation = db_get_conversation_by_id(user_id, conversation_id, db_session)
    if conversation:
        conversation.updated_at = func.now()
        if conversation.title is None or conversation.title == "":
            conversation.title = title
    db_session.commit()
    db_session.refresh(conversation)
    return conversation

def db_delete_conversation(user_id, conversation_id, db_session) -> Conversations:
    conversation = db_get_conversation_by_id(user_id, conversation_id, db_session)
    if conversation:
        db_session.delete(conversation)
        db_session.commit()
    return conversation
