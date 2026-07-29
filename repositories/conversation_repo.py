from model import Conversations


def get_conversations(db_session, conversation_id, user_id) -> Conversations:
    return (db_session.query(Conversations)
            .filter(Conversations.id == conversation_id, Conversations.user_id == user_id).all())


def create_conversation(db_session, conversation: Conversations):
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation
