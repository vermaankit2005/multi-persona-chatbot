"""Push every JSON file in evals/datasets/ up to LangSmith.

One file -> one dataset, named after the file. groundedness.json lands in the
dataset called "groundedness", tool_decision.json in "tool_decision", and so on.
They stay apart because each file is judged by a different UI evaluator.

Run it:

    python evals/examples/upload_datasets.py

Safe to run as many times as you like:

  * dataset is not there  -> create it, upload every row
  * dataset is there      -> upload only the rows that are missing

Every row gets a fixed id built from its "name", which is how a row already on
the server is recognised. LangSmith does not de-duplicate for you.
"""

import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client
from langsmith.utils import LangSmithConflictError

load_dotenv()

DATASET_DIR = Path(__file__).resolve().parents[1] / "datasets"

# Any fixed UUID works. Never change it, or every row gets a new id and the
# side-by-side compare with old experiments breaks.
ID_NAMESPACE = uuid.UUID("6f3a2b10-9c4d-4f7e-8a51-2d0b7c9e4a13")

# Row keys that hold the reference the judge is allowed to see. They arrive in
# the evaluator as `reference_outputs`, not `outputs`.
REFERENCE_KEYS = (
    "retrieval_context",   # groundedness, injection_tool_result
    "expected_output",     # factual_correctness
    "expected_tools",      # tool_decision
    "expected_outcome",    # memory_*, persona_long_thread
)


def example_id(name: str) -> uuid.UUID:
    """Same row name -> same id, on every machine, forever."""
    return uuid.uuid5(ID_NAMESPACE, name)


def to_payload(row: dict, dataset_name: str) -> dict:
    """One JSON row -> the three dicts LangSmith stores.

    The files do not all have the same shape. Single-question rows carry an
    "input". Multi-turn rows carry "turns" plus a "scenario". Both end up here.
    """
    inputs: dict = {}

    if "input" in row:
        inputs["question"] = row["input"]

    for key in ("turns", "scenario", "user_description"):
        if key in row:
            inputs[key] = row[key]

    # Reference keys go in BOTH places, on purpose.
    #  * inputs  - evaluate() hands the target example.inputs only, so this is
    #              the only way the target can echo a reference back out as a
    #              run output. retrieval_context also feeds the fake search
    #              tool from here.
    #  * outputs - still the reference_outputs an offline-only judge reads.
    for key in REFERENCE_KEYS:
        if key in row:
            inputs[key] = row[key]

    outputs = {key: row[key] for key in REFERENCE_KEYS if key in row}

    metadata = {
        "name": row["name"],
        "dataset": dataset_name,
        **row.get("additional_metadata", {}),
    }
    if "comments" in row:
        metadata["comments"] = row["comments"]

    return {"inputs": inputs, "outputs": outputs, "metadata": metadata}


def get_or_create_dataset(client: Client, dataset_name: str):
    """Returns (dataset, is_new). is_new saves a pointless list call."""
    try:
        dataset = client.create_dataset(dataset_name)
        print(f"  dataset {dataset_name!r} did not exist, created it")
        return dataset, True
    except LangSmithConflictError:
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"  dataset {dataset_name!r} already exists")
        return dataset, False


def upload_file(client: Client, path: Path) -> tuple[int, int]:
    """Upload one JSON file. Returns (created, skipped)."""
    dataset_name = path.stem
    rows = json.loads(path.read_text(encoding="utf-8"))

    print(f"\n{path.name}  ({len(rows)} row(s) in the file)")
    dataset, is_new = get_or_create_dataset(client, dataset_name)

    # One round trip, then decide create-or-skip per row locally.
    on_server = (
        set() if is_new
        else {ex.id for ex in client.list_examples(dataset_id=dataset.id)}
    )
    if not is_new:
        print(f"  {len(on_server)} example(s) already up there")

    to_create = []
    skipped = 0

    for row in rows:
        eid = example_id(row["name"])
        if eid in on_server:
            skipped += 1
        else:
            to_create.append({"id": eid, **to_payload(row, dataset_name)})
            print(f"  new      {row['name']}")

    if to_create:
        client.create_examples(dataset_id=dataset.id, examples=to_create)

    stale = on_server - {example_id(row["name"]) for row in rows}
    if stale:
        # Not deleted on purpose. Old experiments still point at these ids.
        print(f"  {len(stale)} example(s) are on the server but not in the file.")
        print("  Delete them by hand if you really want them gone:")
        for eid in stale:
            print(f"    client.delete_example(example_id='{eid}')")

    print(f"  {len(to_create)} created, {skipped} skipped.")
    return len(to_create), skipped


def check_names_are_unique(files: list[Path]) -> None:
    """Ids come from the row name alone, so one name may live in one file only.

    Two files sharing a name would write the same id into two datasets. Better
    to stop here than to find out on the server.
    """
    seen: dict[str, str] = {}
    clashes = []
    for path in files:
        for row in json.loads(path.read_text(encoding="utf-8")):
            if row["name"] in seen:
                clashes.append(f"  {row['name']!r} in {seen[row['name']]} and {path.name}")
            seen[row["name"]] = path.name

    if clashes:
        raise SystemExit("Duplicate row names:\n" + "\n".join(clashes))


def main() -> None:
    files = sorted(DATASET_DIR.glob("*.json"))
    if not files:
        raise SystemExit(f"No JSON files in {DATASET_DIR}")

    check_names_are_unique(files)
    print(f"{len(files)} dataset file(s) in {DATASET_DIR}")

    client = Client()
    created = skipped = 0

    for path in files:
        made, kept = upload_file(client, path)
        created += made
        skipped += kept

    print(f"\nDone. {created} example(s) created, {skipped} already there.")
    print("https://smith.langchain.com/  ->  Datasets")


if __name__ == "__main__":
    main()
