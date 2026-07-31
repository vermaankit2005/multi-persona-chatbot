from model import Messages


# For showing in UI
def db_get_all_messages_for_conversation(conversation_id, db_session) -> list[Messages]:
    return db_session.query(Messages).filter(Messages.conversation_id == conversation_id).all()


# For llm context
def db_get_recent_messages_for_conversation(conversation_id, db_session, limit=10) -> list[Messages]:
    return (db_session.query(Messages)
            .filter(Messages.conversation_id == conversation_id)
            .order_by(Messages.id.desc())
            .limit(limit)
            .all())


# Actual chat messages are stored in the Messages table, which is linked to the Conversations table via conversation_id
def db_create_message(message: Messages, db_session) -> Messages:
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message
