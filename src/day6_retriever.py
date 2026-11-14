"""Dense retrieval from the real Day 06 on-disk Qdrant index."""

import argparse
from pathlib import Path
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models


MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION = "day06_fixed_a"
DIMENSIONS = 384


class Day6Retriever:
    """Read the dev-selected Day 06 A collection with its original query model."""

    def __init__(self, day6_repo: Path) -> None:
        storage = day6_repo / "starter" / "qdrant_storage"
        if not (storage / "meta.json").is_file():
            raise FileNotFoundError(f"Day 06 Qdrant index is missing: {storage}")
        self.client = QdrantClient(path=str(storage))
        try:
            if not self.client.collection_exists(COLLECTION):
                raise ValueError(f"Day 06 collection is missing: {COLLECTION}")
            vector_config = self.client.get_collection(COLLECTION).config.params.vectors
            if vector_config.size != DIMENSIONS or vector_config.distance != models.Distance.COSINE:
                raise ValueError("Day 06 vector configuration does not match the query model")
            self.model = TextEmbedding(model_name=MODEL_NAME)
        except Exception:
            self.client.close()
            raise

    def search(
        self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3,
    ) -> list[dict[str, Any]]:
        if not query.strip() or top_k < 1:
            raise ValueError("query must be nonempty and top_k must be positive")
        if filters and (set(filters) != {"section"} or not isinstance(filters["section"], str)):
            raise ValueError("only a string-valued section filter is supported")
        condition = None
        if filters:
            condition = models.Filter(must=[
                models.FieldCondition(
                    key="section", match=models.MatchValue(value=filters["section"])
                )
            ])
        vector = next(iter(self.model.query_embed(query))).tolist()
        points = self.client.query_points(
            collection_name=COLLECTION,
            query=vector,
            query_filter=condition,
            limit=top_k,
            with_payload=True,
        ).points
        return [
            {
                "id": point.payload["chunk_id"],
                "text": point.payload["text"],
                "source_id": point.payload["document_id"],
                "source": point.payload["source"],
                "page": point.payload["page"],
                "metadata": {
                    key: value for key, value in point.payload.items()
                    if key not in {"chunk_id", "document_id", "source", "page", "text"}
                },
                "score": float(point.score),
            }
            for point in points
        ]

    def close(self) -> None:
        self.client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the Day 06 dense retriever")
    parser.add_argument("--day6-repo", type=Path, required=True)
    parser.add_argument(
        "--query", default="What labor shift helped reduce poverty and inequality from 2010 to 2014?"
    )
    args = parser.parse_args()
    retriever = Day6Retriever(args.day6_repo)
    try:
        hits = retriever.search(args.query)
        if len(hits) != 3:
            raise RuntimeError(f"Expected three real search hits, got {len(hits)}")
        for rank, hit in enumerate(hits, 1):
            print(f"{rank}. PDF page {hit['page']} score={hit['score']:.4f} id={hit['id']}")
    finally:
        retriever.close()


if __name__ == "__main__":
    main()
