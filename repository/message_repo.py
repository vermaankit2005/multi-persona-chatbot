from model import Messages


# For showing in UI. The persona's system prompt is a real row but is never
# rendered, so it is left out here. Oldest first: the order bubbles appear in.
def db_get_all_messages_for_conversation(conversation_id, db_session) -> list[Messages]:
    return (db_session.query(Messages)
            .filter(Messages.conversation_id == conversation_id, Messages.role != "system")
            .order_by(Messages.id)
            .all())


# For llm context. The system row is left out on purpose: it has the lowest id,
# so a sliding window would drop the persona once the chat outgrows `limit`.
def db_get_recent_messages_for_conversation(conversation_id, db_session, limit=20) -> list[Messages]:
    return (db_session.query(Messages)
            .filter(Messages.conversation_id == conversation_id, Messages.role != "system")
            .order_by(Messages.id.desc())
            .limit(limit)
            .all()[::-1])  # Reverse to get oldest first


# The persona prompt, written once when the conversation was created. Fetched
# separately so it can be prepended to every window, however long the chat gets.
def db_get_system_message_for_conversation(conversation_id, db_session) -> Messages:
    return (db_session.query(Messages)
            .filter(Messages.conversation_id == conversation_id, Messages.role == "system")
            .order_by(Messages.id)
            .first())

def db_create_messages(messages: list[Messages], db_session) -> list[Messages]:
    db_session.add_all(messages)
    db_session.commit()
    for message in messages:
        db_session.refresh(message)
    return messages