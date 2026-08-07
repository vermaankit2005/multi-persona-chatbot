from typing import Tuple

from deps import Role
from model import Conversations, Messages
from repository.conversation_repo import db_create_conversation, db_get_conversation_by_id, db_delete_conversation
from repository.message_repo import db_get_all_messages_for_conversation, db_create_messages
from repository.persona_repo import db_get_persona


def create_conversation(user_id, persona_key, db_session) -> Conversations:
    persona_in_db = db_get_persona(persona_key, db_session)  # Fetch all personas from the database
    if not persona_in_db:
        raise LookupError(
            "Persona not found, Please provide a valid persona key.")  # Raise an error if the persona does not exist
    # Create a new conversation for the user with the specified persona
    conversation = db_create_conversation(Conversations(user_id=user_id, persona_key=persona_key), db_session)
    db_create_messages(
        [Messages(
            conversation_id=conversation.id,
            role=Role.SYSTEM.value,
            content=persona_in_db.system_prompt
        )],
        db_session=db_session
    )
    return conversation


def get_messages_for_conversation(user_id, conversation_id, db_session) \
        -> Tuple[Conversations, list[Messages]]:
    conversation = db_get_conversation_by_id(user_id, conversation_id, db_session)  # Ensure the conversation exists
    if not conversation:
        raise LookupError(
            "Conversation not found, Please provide a valid conversation id.")  # Raise an error if the conversation does not exist

    messages = db_get_all_messages_for_conversation(conversation_id, db_session)
    return conversation, messages  # Return the conversation and its messages


def delete_conversation(user_id, conversation_id, db_session) -> Conversations:
    # Delete the conversation and its messages
    return db_delete_conversation(user_id, conversation_id, db_session)