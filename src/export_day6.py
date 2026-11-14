"""Export the Day 06 A collection for the official Day 07 converter.

Run from the Day 07 repository root. The output is local generated data.
"""

import argparse
import json
from pathlib import Path

from qdrant_client import QdrantClient


COLLECTION = "day06_fixed_a"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day6-repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    store_path = args.day6_repo / "starter" / "qdrant_storage"
    benchmark_path = args.day6_repo / "benchmark" / "questions.json"
    summary_path = args.day6_repo / "starter" / "results" / "ingestion_summary.json"
    if not store_path.joinpath("meta.json").is_file():
        raise FileNotFoundError(f"Day 06 Qdrant index is missing: {store_path}")
    questions = json.loads(benchmark_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    client = QdrantClient(path=str(store_path))
    try:
        if not client.collection_exists(COLLECTION):
            raise ValueError(f"Day 06 collection is missing: {COLLECTION}")
        chunks = []
        offset = None
        while True:
            points, offset = client.scroll(
                collection_name=COLLECTION,
                offset=offset,
                limit=100,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload = point.payload
                chunks.append({
                    "chunk_id": payload["chunk_id"],
                    "document_id": payload["document_id"],
                    "source": payload["source"],
                    "page": payload["page"],
                    "text": payload["text"],
                    "metadata": {
                        key: value for key, value in payload.items()
                        if key not in {"chunk_id", "document_id", "source", "page", "text"}
                    },
                })
            if offset is None:
                break
    finally:
        client.close()

    chunks.sort(key=lambda chunk: chunk["chunk_id"])
    if len(chunks) != summary["chunk_counts"]["A"]:
        raise ValueError("Exported point count does not match Day 06 ingestion summary")
    if len({chunk["chunk_id"] for chunk in chunks}) != len(chunks):
        raise ValueError("Duplicate Day 06 chunk IDs")
    if len(questions) != 20:
        raise ValueError("Expected the frozen 20-question Day 06 benchmark")

    args.output.mkdir(parents=True, exist_ok=True)
    for name, rows in (("chunks.json", chunks), ("questions.json", questions)):
        args.output.joinpath(name).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Exported {len(chunks)} real Day 06 chunks and {len(questions)} questions to {args.output}")


if __name__ == "__main__":
    main()
