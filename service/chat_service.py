from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from conversion.conversion import to_langchain
from deps import Role
from model import Messages
from repository.conversation_repo import db_get_conversation_by_id, db_update_conversation_title
from repository.message_repo import db_get_recent_messages_for_conversation, db_get_system_message_for_conversation, \
    db_create_messages


def send_message(user_id, agent, message_content: str, conversation_id, db) -> tuple[Messages, Messages]:
    conversation = db_get_conversation_by_id(user_id, conversation_id, db)
    if conversation is None:
        raise LookupError(f"Conversation not found for user_id: {user_id}, conversation_id: {conversation_id}")

    # 1. Add the latest human message to the database
    latest_human_message = Messages(
        conversation_id=conversation_id,
        role=Role.USER.value,
        content=message_content
    )

    message_for_agent = db_get_recent_messages_for_conversation(conversation_id, db)
    system_message = db_get_system_message_for_conversation(conversation_id, db)

    if system_message is not None:
        message_for_agent = [system_message, *message_for_agent,
                             latest_human_message]  # Add the latest human message to the context

    # 3. Store the latest human message in the database
    langchain_messages = to_langchain(message_for_agent)

    # 6. Invoke the agent with the messages and get the assistant's response
    assistant_response = agent.invoke({"messages": langchain_messages}, streaming=True)

    latest_assistant_message = Messages(
        conversation_id=conversation_id,
        role=Role.ASSISTANT.value,
        content=assistant_response["messages"][-1].content
        # Assuming the last message in the response is the assistant's reply
    )

    db_create_messages([latest_human_message, latest_assistant_message], db)

    # 7. Update the conversation title and updated_at based on the latest human message
    touch_conversation(user_id, conversation_id, message_content, db)

    return latest_human_message, latest_assistant_message


def touch_conversation(user_id, conversation_id, message_content: str, db):
    title = message_content[:50] + "..." if len(message_content) > 50 else message_content
    db_update_conversation_title(user_id, title, conversation_id, db)
