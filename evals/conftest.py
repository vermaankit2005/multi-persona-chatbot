import pytest

from db import get_db_session
from llm.agent import build_agent
from model import Users, Conversations
from repository.user_repo import db_get_or_create_user
from service.conversation_service import create_conversation


#  Test class to create the database and tables for testing
@pytest.fixture(scope="session")
def eval_db_session():
    session = next(get_db_session())
    try:
        yield session  # Provide the session to the tests
    finally:
        session.close()  # Clean up after tests


@pytest.fixture(scope="session")
def persona_key():
    return "grumpy_pirate"


# Create dummy user
@pytest.fixture(scope="session")
def eval_user(eval_db_session) -> Users:
    print("Creating or getting dummy user for testing...")
    user = db_get_or_create_user(provider="dev", provider_user_id="test_user_id", email="test@example.com",
                                 db_session=eval_db_session)
    yield user
    eval_db_session.delete(user)
    eval_db_session.commit()


# Create conversation for dummy user
@pytest.fixture(scope="function")
def eval_create_dummy_conversation(eval_db_session, persona_key, eval_user) -> Conversations:
    print("Creating dummy conversation for testing...")
    conversation = create_conversation(eval_user.id, persona_key, eval_db_session)

    yield conversation

    print("Deleting dummy conversation...")
    eval_db_session.delete(conversation)
    eval_db_session.commit()


# Create conversation for dummy user
@pytest.fixture(scope="module")
def eval_create_dummy_conversation_module_accumulated(eval_db_session, persona_key, eval_user) -> Conversations:
    print("Creating dummy conversation for testing...")
    conversation = create_conversation(eval_user.id, persona_key, eval_db_session)

    yield conversation

    print("Deleting dummy conversation...")
    eval_db_session.delete(conversation)
    eval_db_session.commit()


@pytest.fixture(scope="session")
def eval_agent():
    print("Building agent for testing...")
    return build_agent()
