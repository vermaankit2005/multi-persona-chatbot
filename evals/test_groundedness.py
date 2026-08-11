from deepeval.dataset import EvaluationDataset
from deepeval.evaluate import evaluate
from deepeval.metrics import GEval
from deepeval.models import LocalModel
from deepeval.test_case import SingleTurnParams, LLMTestCase
from langchain_tavily import TavilySearch

from config import settings
from llm.agent import build_agent
from service.chat_service import send_message

judge = LocalModel(
    model="deepseek/deepseek-v4-flash",
    api_key=settings.OPENROUTE_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


# def test_groundedness(eval_user, eval_db_session, normal_agent_prompt):
#     dataset = EvaluationDataset()
#     dataset.add_goldens_from_json_file("evals/datasets/groundedness.json")
#
#     groundedness_metric = GEval(
#         name="groundedness",
#         model=judge,
#         threshold=1,
#         criteria="""
#         You are a judge that evaluates the groundedness of an LLM's response to a user's question.
#         Inputs:
#             Input: User's question: {input}
#             Retrieval context: Context retrieved from web search: {retrieval_context}
#             Actual Output: LLM's response: {actual_output}
#         """,
#         evaluation_params=[
#             SingleTurnParams.INPUT,
#             SingleTurnParams.RETRIEVAL_CONTEXT,
#             SingleTurnParams.ACTUAL_OUTPUT
#         ]
#     )
#
#     test_cases = []
#
#     for golden in dataset.goldens:
#         agent = build_fake_agent(golden.retrieval_context)  # only the fake tool
#
#         messages = [
#             SystemMessage(content=normal_agent_prompt),
#             HumanMessage(content=golden.input),
#             AIMessage(content="", tool_calls=[{
#                 "id": "123", "name": "tavily_search", "args": {"query": golden.input}}]),
#             ToolMessage(content="\n".join(golden.retrieval_context), tool_call_id="123"),
#         ]
#
#         result = agent.invoke({"messages": messages})
#         answer = result["messages"][-1].content
#
#         test_cases.append(LLMTestCase(
#             input=golden.input,
#             actual_output=answer,
#             retrieval_context=golden.retrieval_context,
#         ))
#
#     evaluate(test_cases=test_cases, metrics=[groundedness_metric])


def test_groundedness(eval_user, make_conversation, eval_db_session, monkeypatch):
    dataset = EvaluationDataset()
    dataset.add_goldens_from_json_file("evals/datasets/groundedness.json")

    groundedness_metric = GEval(
        name="groundedness",
        model=judge,
        threshold=1,
        criteria="""
                You are a judge that evaluates the groundedness of an LLM's response to a user's question.
                Inputs:
                    Input: User's question: {input}
                    Retrieval context: Context retrieved from web search: {retrieval_context}
                    Actual Output: LLM's response: {actual_output}
                """,
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.RETRIEVAL_CONTEXT,
            SingleTurnParams.ACTUAL_OUTPUT
        ]
    )

    holder = {"context": []}  # current row's golden context

    def fake_run(self, query, **kwargs):  # replaces the web call only
        return {"query": query,
                "results": [{"content": c} for c in holder["context"]]}

    monkeypatch.setattr(TavilySearch, "_run", fake_run)

    agent = build_agent()  # YOUR real agent. no copy, no drift.
    test_cases = []

    for golden in dataset.goldens:
        holder["context"] = golden.retrieval_context
        conv = make_conversation()

        _, assistant, tools_called = send_message(
            eval_user.id, agent, golden.input, conv.id, eval_db_session)

        if "tavily_search" in tools_called:  # only score rows where it searched
            test_cases.append(LLMTestCase(
                input=golden.input,
                actual_output=assistant.content,
                retrieval_context=golden.retrieval_context,
            ))

    evaluate(test_cases=test_cases, metrics=[groundedness_metric])
