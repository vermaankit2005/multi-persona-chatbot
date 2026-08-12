"""Push evals/datasets/groundedness.json up to a LangSmith dataset.

The JSON file is the boss. Edit it, then run this:

    python evals/examples/upload_groundedness_dataset.py

Safe to run as many times as you like. Every row gets a fixed id built from
its "name", so a row that is already up there is updated in place instead of
being added a second time. LangSmith does not de-duplicate for you.
"""

import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langsmith.utils import LangSmithConflictError

load_dotenv()

DATASET_NAME = "groundedness"
DATASET_FILE = Path(__file__).resolve().parents[1] / "datasets" / "groundedness.json"

# Any fixed UUID works. Never change it, or every row gets a new id and the
# side-by-side compare with old experiments breaks.
ID_NAMESPACE = uuid.UUID("6f3a2b10-9c4d-4f7e-8a51-2d0b7c9e4a13")


def example_id(name: str) -> uuid.UUID:
    """Same row name -> same id, on every machine, forever."""
    return uuid.uuid5(ID_NAMESPACE, name)


def to_payload(row: dict) -> dict:
    """One JSON row -> the three dicts LangSmith stores."""
    return {
        # inputs: everything the agent needs to answer.
        # retrieval_context rides along so the fake search tool can serve it.
        "inputs": {
            "question": row["input"],
            "retrieval_context": row["retrieval_context"],
        },
        # outputs: the reference the judge is allowed to see. This arrives in
        # the evaluator as `reference_outputs`, not `outputs`.
        "outputs": {
            "retrieval_context": row["retrieval_context"]
        },
        "metadata": {
            "name": row["name"], **row.get("additional_metadata", {})
        },
    }


def get_or_create_dataset(client: Client):
    try:
        dataset = client.create_dataset(DATASET_NAME)
        print(f"Created dataset {DATASET_NAME!r}")
        return dataset
    except LangSmithConflictError:
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        print(f"Using existing dataset {DATASET_NAME!r}")
        return dataset


def main() -> None:
    rows = json.loads(DATASET_FILE.read_text(encoding="utf-8"))

    client = Client()
    dataset = get_or_create_dataset(client)

    # One round trip, then decide update-or-create per row locally.
    already_there = {ex.id for ex in client.list_examples(dataset_id=dataset.id)}

    to_create = []
    updated = 0

    for row in rows:
        eid = example_id(row["name"])
        payload = to_payload(row)

        if eid in already_there:
            client.update_example(example_id=eid, **payload)
            updated += 1
            print(f"  updated  {row['name']}")
        else:
            to_create.append({"id": eid, **payload})
            print(f"  new      {row['name']}")

    if to_create:
        client.create_examples(dataset_id=dataset.id, examples=to_create)

    stale = already_there - {example_id(r["name"]) for r in rows}
    if stale:
        # Not deleted on purpose. Old experiments still point at these ids.
        print(f"\n{len(stale)} example(s) are on the server but not in the JSON file.")
        print("Delete them by hand if you really want them gone:")
        for eid in stale:
            print(f"  client.delete_example(example_id='{eid}')")

    print(f"\nDone. {updated} updated, {len(to_create)} created.")
    print(f"https://smith.langchain.com/  ->  Datasets  ->  {DATASET_NAME}")


if __name__ == "__main__":
    main()
