
import json
import os

import pytest
from langchain_tavily import TavilySearch
from langsmith import Client
from openai import OpenAI

from config import settings
from llm.agent import build_agent
from service.chat_service import send_message
import load_dotenv

load_dotenv.load_dotenv()

DATASET_NAME = "groundedness"  # must match evals/examples/upload_groundedness_dataset.py

judge = OpenAI(
    api_key=settings.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

JUDGE_MODEL = "openai/gpt-oss-120b"

# JUDGE_PROMPT = """
#     You are a judge that scores how grounded an answer is.
#
#     The answer is grounded when every claim in it comes from the search results.
#     Saying "the search results do not cover that" is grounded and good.
#     Adding a fact that is not in the search results is not grounded, even if the
#     fact is true in the real world. Ignore tone and style.
#
#     User's question:
#     {question}
#
#     Search results the model was given:
#     {context}
#
#     The model's answer:
#     {answer}
#
#     Reply with JSON only: {{"score": 1 or 0, "reason": "one short sentence"}}
#     score 1 = fully grounded, score 0 = anything invented.
# """


# def groundedness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
#     """LLM-as-judge. Replaces DeepEval's GEval metric."""
#     prompt = JUDGE_PROMPT.format(
#         question=inputs["question"],
#         context="\n".join(reference_outputs["retrieval_context"]),
#         answer=outputs["answer"],
#     )
#
#     reply = judge.chat.completions.create(
#         model=JUDGE_MODEL,
#         messages=[{"role": "user", "content": prompt}],
#         response_format={"type": "json_object"},
#     )
#     verdict = json.loads(reply.choices[0].message.content)
#
#     return {
#         "key": "groundedness",
#         "score": verdict["score"],
#         "comment": verdict["reason"],
#     }


# def searched(outputs: dict) -> dict:
#     """Did the agent actually reach for the web tool?
#
#     DeepEval skipped these rows. LangSmith runs every row, so score it instead
#     of hiding it. A row that scores 0 here makes any groundedness score noise.
#     """
#     return {
#         "key": "used_search",
#         "score": int("tavily_search" in outputs["tools_called"]),
#     }


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
        conversation = make_conversation()

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

    results = Client().evaluate(
        target,
        data=DATASET_NAME,
        # evaluators=[groundedness, searched],
        experiment_prefix="groundedness",
        # Must stay 1. `holder` is shared state and the SQLAlchemy session is
        # not thread safe, so parallel rows would cross wires.
        max_concurrency=1,
    )

    print(f"\nResults: {results.url}")

    # scores = {}
    # for row in results:
    #     name = row["example"].metadata.get("name")
    #     scores[name] = {
    #         result.key: result.score
    #         for result in row["evaluation_results"]["results"]
    #     }
    #     print(f"  {name}: {scores[name]}")
    #
    # assert scores, "no rows were scored, is the dataset empty?"
    #
    # failed = [name for name, s in scores.items() if s.get("groundedness") != 1]
    # assert not failed, f"not grounded: {failed}  see {results.url}"
