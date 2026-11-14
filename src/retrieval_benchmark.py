"""Compare dense, TF-IDF and RRF hybrid retrieval on the fixed Day 7 benchmark."""

import argparse
import hashlib
import json
import math
import statistics
import time
from collections import Counter
from pathlib import Path

from src.day6_retriever import Day6Retriever
from starter.baseline import tokenize


def matches_filter(chunk: dict, filters: dict | None) -> bool:
    return all(chunk["metadata"].get(key) == value for key, value in (filters or {}).items())


class LexicalRetriever:
    def __init__(self, chunks: list[dict]) -> None:
        self.chunks = chunks
        counts = [Counter(tokenize(chunk["text"])) for chunk in chunks]
        document_frequency = Counter(term for row in counts for term in row)
        self.idf = {
            term: math.log((1 + len(chunks)) / (1 + frequency)) + 1
            for term, frequency in document_frequency.items()
        }
        self.vectors = [self._vector(row) for row in counts]

    def _vector(self, counts: Counter) -> dict[str, float]:
        vector = {term: count * self.idf[term] for term, count in counts.items()
                  if term in self.idf}
        norm = math.sqrt(sum(value * value for value in vector.values())) or 1
        return {term: value / norm for term, value in vector.items()}

    def search(self, query: str, *, filters: dict | None = None,
               top_k: int = 3) -> list[dict]:
        query_vector = self._vector(Counter(tokenize(query)))
        hits = []
        for chunk, vector in zip(self.chunks, self.vectors):
            if not matches_filter(chunk, filters):
                continue
            score = sum(value * vector.get(term, 0) for term, value in query_vector.items())
            if score > 0:
                hits.append({**chunk, "score": score})
        return sorted(hits, key=lambda hit: (-hit["score"], hit["id"]))[:top_k]


def rrf(dense_hits: list[dict], lexical_hits: list[dict],
        *, constant: int = 60, top_k: int = 3) -> list[dict]:
    """Fuse ranks, not the incompatible cosine and TF-IDF scores."""
    fused: dict[str, dict] = {}
    for name, hits in (("dense", dense_hits), ("tfidf", lexical_hits)):
        for rank, hit in enumerate(hits, start=1):
            item = fused.setdefault(hit["id"], {**hit, "score": 0.0, "ranks": {}})
            item["score"] += 1 / (constant + rank)
            item["ranks"][name] = rank
    return sorted(fused.values(), key=lambda hit: (-hit["score"], hit["id"]))[:top_k]


def pack_context(hits: list[dict], budget_chars: int) -> tuple[str, list[str]]:
    blocks = []
    ids = []
    for hit in hits:
        block = f"[{hit['id']} | {hit['source']} | page {hit['page']}]\n{hit['text']}"
        if len("\n\n".join(blocks + [block])) <= budget_chars:
            blocks.append(block)
            ids.append(hit["id"])
    return "\n\n".join(blocks), ids


def evidence_hit(hit: dict, gold: list[dict]) -> bool:
    return any(hit["source_id"] == item["source_id"]
               and hit["page"] == item["page"]
               and item["evidence"] in hit["text"] for item in gold)


def evaluate(method: str, questions: list[dict], dense: Day6Retriever,
             lexical: LexicalRetriever, budget_chars: int) -> tuple[dict, list[dict]]:
    traces = []
    for question in questions:
        query = question["question"]
        filters = question.get("filter")
        start = time.perf_counter()
        if method == "dense":
            hits = dense.search(query, filters=filters, top_k=3)
            candidates = len(hits)
        elif method == "tfidf":
            hits = lexical.search(query, filters=filters, top_k=3)
            candidates = len(hits)
        else:
            dense_candidates = dense.search(query, filters=filters, top_k=20)
            lexical_candidates = lexical.search(query, filters=filters, top_k=20)
            candidates = len({hit["id"] for hit in dense_candidates + lexical_candidates})
            hits = rrf(dense_candidates, lexical_candidates, top_k=3)
        context, context_ids = pack_context(hits, budget_chars)
        elapsed_ms = (time.perf_counter() - start) * 1000
        answerable = question.get("answerable") is not False
        marked = [
            {**hit, "hit": evidence_hit(hit, question["gold"]) if answerable else None}
            for hit in hits
        ]
        traces.append({
            "query_id": question["id"], "split": question["split"],
            "question": query, "filter": filters, "method": method,
            "answerable": answerable, "candidate_count": candidates,
            "top_k": 3, "budget_chars": budget_chars,
            "results": marked, "context": context, "context_ids": context_ids,
            "context_chars": len(context), "elapsed_ms": elapsed_ms,
            "hit1": bool(marked and marked[0]["hit"]) if answerable else None,
            "hit3": any(hit["hit"] for hit in marked) if answerable else None,
            "context_hit": any(hit["hit"] and hit["id"] in context_ids
                               for hit in marked) if answerable else None,
        })
    positives = [trace for trace in traces if trace["answerable"]]
    n = len(positives)
    summary = {
        "method": method, "split": questions[0]["split"],
        "answerable_n": n, "no_evidence_n": len(traces) - n,
        "hit1": sum(trace["hit1"] for trace in positives),
        "hit3": sum(trace["hit3"] for trace in positives),
        "context_evidence": sum(trace["context_hit"] for trace in positives),
        "budget_chars": budget_chars, "candidate_limit_per_retriever": 20 if method == "hybrid_rrf" else 3,
        "mean_candidates": statistics.mean(trace["candidate_count"] for trace in traces),
        "median_query_ms": statistics.median(trace["elapsed_ms"] for trace in traces),
        "total_query_seconds": sum(trace["elapsed_ms"] for trace in traces) / 1000,
        "api_cost_usd": 0,
    }
    for name in ("hit1", "hit3", "context_evidence"):
        summary[name + "_rate"] = summary[name] / n
    return summary, traces


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--day6-repo", required=True, type=Path)
    parser.add_argument("--chunks", type=Path, default=Path("starter/data/converted/chunks.json"))
    parser.add_argument("--questions", type=Path, default=Path("data/questions.json"))
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--methods", nargs="+", choices=("tfidf", "dense", "hybrid_rrf"),
                        default=("tfidf", "dense", "hybrid_rrf"))
    parser.add_argument("--lock", type=Path, default=Path("report/agent_dev/selected_config.json"))
    parser.add_argument("--budget-chars", type=int, default=2400)
    parser.add_argument("--output", type=Path, default=Path("starter/results/day7-retrieval-dev"))
    args = parser.parse_args()
    if args.budget_chars < 1:
        parser.error("--budget-chars must be positive")
    if args.split == "test":
        lock = json.loads(args.lock.read_text(encoding="utf-8"))
        if (set(args.methods) != {"dense", "hybrid_rrf"}
                or len(args.methods) != 2 or args.budget_chars != 2400):
            parser.error("Test retrieval must compare only frozen dense and hybrid at the dev 2400-character budget")
        if (hashlib.sha256(args.questions.read_bytes()).hexdigest() != lock["benchmark_sha256"]
                or hashlib.sha256(args.chunks.read_bytes()).hexdigest() != lock["exported_chunks_sha256"]):
            parser.error("Test benchmark/corpus does not match the frozen dev selection")
    chunks = json.loads(args.chunks.read_text(encoding="utf-8"))
    all_questions = json.loads(args.questions.read_text(encoding="utf-8"))
    questions = [question for question in all_questions if question["split"] == args.split]
    if not questions:
        parser.error(f"No {args.split} questions")
    started = time.perf_counter()
    lexical = LexicalRetriever(chunks)
    lexical_build_seconds = time.perf_counter() - started
    dense = Day6Retriever(args.day6_repo)
    try:
        rows = []
        for method in args.methods:
            summary, traces = evaluate(method, questions, dense, lexical, args.budget_chars)
            summary["lexical_build_seconds"] = lexical_build_seconds if method != "dense" else 0
            rows.append(summary)
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / f"{method}_traces.json").write_text(
                json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        (args.output / "summary.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    finally:
        dense.close()


if __name__ == "__main__":
    main()
