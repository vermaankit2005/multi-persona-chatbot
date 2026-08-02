# to_langchain(conversation, message_rows)  →  [SystemMessage(persona), HumanMessage, AIMessage, ...]
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage

from deps import Role
from model import Messages


def to_langchain(message_rows: list[Messages]) -> list[BaseMessage]:
    """
    Convert a list of Messages to a list of LangChain BaseMessage objects.
    """
    langchain_messages = []

    # Add the rest of the messages in order
    for msg in message_rows:
        if msg.role == Role.USER.value:
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == Role.ASSISTANT.value:
            langchain_messages.append(AIMessage(content=msg.content))
        elif msg.role == Role.SYSTEM.value:
            langchain_messages.append(SystemMessage(content=msg.content))
            continue

    return langchain_messages
