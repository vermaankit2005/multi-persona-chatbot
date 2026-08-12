from uuid import UUID

from langsmith import traceable, get_current_run_tree
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from conversion.conversion import to_langchain
from deps import Role
from model import Messages
from repository.conversation_repo import db_update_conversation_title
from repository.message_repo import db_get_recent_messages_for_conversation, db_get_system_message_for_conversation, \
    db_create_messages
from schemas import TokenEvent, DoneEvent
from schemas.message import ToolCallEvent, ErrorEvent


def _sse(event: str, payload: BaseModel) -> str:
    """One server-sent event: a named event plus a single JSON data line."""
    return f"event: {event}\ndata: {payload.model_dump_json()}\n\n"


def _collect(events: list[dict]) -> dict:
    answer, tools_called, context = "", [], []
    for event in events:
        if event["type"] == "token":
            answer += event["text"]
        elif event["type"] == "summary":  # this is event which happens after the streaming of the complete answer
            tools_called = event["tools_called"]
            context = event["context"]
    # "reference" is empty on live traffic. Same reason as the sync path: the
    # shared evaluator maps to outputs.reference and a missing key breaks it.
    return {"answer": answer, "context": context, "tools_called": tools_called}


# Yields plain dicts, not wire text. _sse formatting happens one level up in
# send_message_stream, so reduce_fn reads fields instead of parsing SSE back
# apart - and changing the wire format cannot break the trace.
@traceable(name="send_message_stream",
           process_inputs=lambda inputs: {
               "question": inputs["message_content"],
           },
           reduce_fn=_collect)
async def _stream_events(user_id, agent, message_content: str, conversation_id, persona_key, db):
    # 1. Add the latest human message to the database

    run_tree = get_current_run_tree()
    if run_tree is not None:
        run_tree.add_metadata({
            "conversation_id": str(conversation_id),
        })

    latest_human_message = Messages(
        conversation_id=conversation_id,
        role=Role.USER.value,
        content=message_content
    )

    message_for_agent = await run_in_threadpool(db_get_recent_messages_for_conversation, conversation_id, db)
    system_message = await run_in_threadpool(db_get_system_message_for_conversation, conversation_id, db)

    # Add the latest human message to the context
    if system_message is not None:
        message_for_agent = [system_message, *message_for_agent, latest_human_message]

    # 3. Store the latest human message in the database
    langchain_messages = to_langchain(message_for_agent)

    # 6. Invoke the agent with the messages and get the assistant's response
    stream = await agent.astream_events({"messages": langchain_messages}, version="v3")

    assistant_response_content = ""

    try:
        async for message in stream.messages:
            async for delta in message.text:
                assistant_response_content += delta
                yield {"type": "token", "text": delta}
            for call in await message.tool_calls:
                print(f"Tool call: {call['name']} with args: {call['args']}")
                yield {"type": "tool_call", "name": call["name"], "args": call["args"]}

        final_state = await stream.output()
        tool_messages = [m for m in final_state["messages"] if m.type == "tool"]
        yield {
            "type": "summary",
            "tools_called": [m.name for m in tool_messages],
            "context": [m.content for m in tool_messages],
        }

        user_row, assistant_row = await run_in_threadpool(save_assistant_response,
                                                          assistant_response_content, conversation_id, db,
                                                          message_content, user_id
                                                          )
        yield {
            "type": "done",
            "user_message_id": user_row.id,
            "assistant_message_id": assistant_row.id,
        }
    except Exception as exc:
        yield {"type": "error", "detail": str(exc)}


# The route streams this one. It only turns events into wire format - the
# "summary" event is for the trace and is deliberately not sent to the client.
async def send_message_stream(user_id, agent, message_content: str, conversation_id, persona_key, db):
    async for event in _stream_events(user_id, agent, message_content, conversation_id, persona_key, db):
        kind = event["type"]
        if kind == "token":
            yield _sse("token", TokenEvent(text=event["text"]))
        elif kind == "tool_call":
            yield _sse("tool_call", ToolCallEvent(name=event["name"], args=event["args"]))
        elif kind == "done":
            yield _sse("done", DoneEvent(
                user_message_id=event["user_message_id"],
                assistant_message_id=event["assistant_message_id"],
            ))
        elif kind == "error":
            yield _sse("error", ErrorEvent(detail=event["detail"]))


def save_assistant_response(assistant_response_content,
                            conversation_id: UUID,
                            db: Session,
                            message_content: str,
                            user_id: UUID) -> Messages:
    # 1. Add the latest human message to the database

    latest_human_message = Messages(
        conversation_id=conversation_id,
        role=Role.USER.value,
        content=message_content
    )

    latest_assistant_message = Messages(
        conversation_id=conversation_id,
        role=Role.ASSISTANT.value,
        content=assistant_response_content
        # Assuming the last message in the response is the assistant's reply
    )

    db_create_messages([latest_human_message, latest_assistant_message], db)

    # 7. Update the conversation title and updated_at based on the latest human message
    touch_conversation(user_id, conversation_id, latest_human_message.content, db)

    return latest_human_message, latest_assistant_message


def touch_conversation(user_id, conversation_id, message_content: str, db):
    title = message_content[:50] + "..." if len(message_content) > 50 else message_content
    db_update_conversation_title(user_id, title, conversation_id, db)
