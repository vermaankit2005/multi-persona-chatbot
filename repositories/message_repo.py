from model import Conversations, Messages

# For showing in UI
def get_all_messages_for_conversation(db_session, conversation_id) -> list[Messages]:
    return db_session.query(Messages).filter(Conversations.id == conversation_id).all()


# For llm context
def get_recent_messages_for_conversation(db_session, conversation_id, limit=10) -> list[Messages]:
    return (db_session.query(Messages)
            .filter(Messages.conversation_id == conversation_id)
            .order_by(Messages.id.desc())
            .limit(limit)
            .all())

# Actual chat me
def create_message(db_session, message: Messages):
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message
