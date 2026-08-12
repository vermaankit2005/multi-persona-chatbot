import os

import load_dotenv
import pytest
from langchain_tavily import TavilySearch
from langsmith import Client

from evals.conftest import persona_key
from llm.agent import build_agent
from service.chat_service import send_message

load_dotenv.load_dotenv()

DATASET_NAME = "groundedness"  # must match a file name in evals/datasets/, uploaded by evals/examples/upload_datasets.py


@pytest.mark.skipif(
    not os.getenv("LANGCHAIN_API_KEY"),
    reason="LANGCHAIN_API_KEY is not set",
)
def test_groundedness_langsmith(eval_user, make_conversation, eval_db_session, monkeypatch):
    holder = {"context": []}  # the current row's golden context

    def fake_run(self, query, **kwargs):  # replaces the web call only
        return {
            "query": query,
            "results": [{"content": c} for c in holder["context"]],
        }

    monkeypatch.setattr(TavilySearch, "_run", fake_run)

    agent = build_agent()  # YOUR real agent. no copy, no drift.

    def target(inputs: dict) -> dict:
        holder["context"] = inputs["retrieval_context"]
        conversation = make_conversation(persona_key = "normal")

        _, assistant, tools_called, retrieved_context = send_message(
            eval_user.id, agent, inputs["question"], conversation.id, eval_db_session
        )
        # Same three keys the production trace logs, so one UI evaluator with one
        # variable mapping scores both this experiment and live traffic.
        return {
            "answer": assistant.content,
            "context": retrieved_context,
            "tools_called": list(tools_called),
        }

    # Evaluator comes from the langsmith UI/Platform, not the code.
    results = Client().evaluate(
        target,
        data=DATASET_NAME,
        experiment_prefix="groundedness",
        max_concurrency=1,
    )

    print(f"\nResults: {results.url}")
