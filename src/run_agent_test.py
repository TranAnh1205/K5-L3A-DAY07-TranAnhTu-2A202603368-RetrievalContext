"""Evaluate baseline and frozen selected agent on the held-out Day 7 test split."""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from starter.agentic import run_agent
from src.real_agent import ChatController, SearchTool, estimate_api_cost
from src.run_agent_dev import write_json


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run locked Day 7 test configuration")
    parser.add_argument("--day6-repo", required=True, type=Path)
    parser.add_argument("--role", required=True, choices=("baseline", "selected"))
    parser.add_argument("--questions", type=Path, default=Path("data/questions.json"))
    parser.add_argument("--chunks", type=Path, default=Path("starter/data/converted/chunks.json"))
    parser.add_argument("--lock", type=Path, default=Path("report/agent_dev/selected_config.json"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    if sha256(args.questions) != lock["benchmark_sha256"]:
        parser.error("Test benchmark differs from the frozen dev selection")
    if sha256(args.chunks) != lock["exported_chunks_sha256"]:
        parser.error("Test corpus differs from the frozen dev selection")
    if lock["method"] != "hybrid_rrf" or lock["selection_split"] != "dev":
        parser.error("Selected configuration is not the frozen dev-selected hybrid")
    method = "dense" if args.role == "baseline" else lock["method"]
    model = lock["model"]
    top_k = lock["top_k"]
    max_searches = lock["max_searches"]
    budget_chars = lock["context_budget_chars"]
    citation_retries = lock["citation_retries"]
    if (top_k, max_searches, budget_chars, citation_retries) != (3, 2, 4000, 0):
        parser.error("Locked parameters changed from the dev runs")
    questions = [q for q in json.loads(args.questions.read_text(encoding="utf-8"))
                 if q["split"] == "test"]
    if len(questions) != 7:
        parser.error("Expected the frozen 7-case test split")

    controller_config = {
        "base_url": "https://api.openai.com/v1", "model": model,
        "api_key": os.environ.get("OPENAI_API_KEY"), "timeout_seconds": 120,
    }
    retriever = SearchTool(method=method, day6_repo=args.day6_repo,
                           chunks_path=args.chunks)
    traces: list[dict] = []
    try:
        for question in questions:
            controller = ChatController(**controller_config)
            filters = question.get("filter")
            started = time.perf_counter()
            try:
                # The model and retriever receive question text/filter only.
                result = run_agent(
                    question["question"], controller, retriever,
                    filters=filters, max_searches=max_searches,
                    top_k=top_k, budget=budget_chars,
                    max_citation_repairs=citation_retries,
                )
            except Exception as error:
                result = {"status": "error", "answer": "", "citations": [],
                          "events": retriever.calls,
                          "error": f"{type(error).__name__}: {error}"}
            trace = {
                "query_id": question["id"], "split": "test", "question": question["question"],
                "filter": filters, "role": args.role, "method": method,
                "model": model, "top_k": top_k, "max_searches": max_searches,
                "budget_chars": budget_chars, "citation_retries": citation_retries,
                "model_calls": controller.calls, "tool_calls": retriever.calls,
                "elapsed_ms": (time.perf_counter() - started) * 1000,
                "api_cost_usd": estimate_api_cost(model, controller.calls),
                **result,
            }
            traces.append(trace)
            write_json(args.output / "traces.json", traces)
            print(f"{question['id']} {trace['status']} searches={len(trace['tool_calls'])} "
                  f"cost={trace['api_cost_usd']}", flush=True)
            retriever.calls = []
    finally:
        retriever.close()

    costs = [trace["api_cost_usd"] for trace in traces]
    summary = {
        "split": "test", "role": args.role, "method": method, "model": model,
        "top_k": top_k, "max_searches": max_searches,
        "citation_retries": citation_retries, "budget_chars": budget_chars,
        "cases": len(traces),
        "status_counts": {status: sum(t["status"] == status for t in traces)
                          for status in ("answered", "abstain", "error")},
        "total_searches": sum(len(t["tool_calls"]) for t in traces),
        "total_model_calls": sum(len(t["model_calls"]) for t in traces),
        "total_elapsed_seconds": sum(t["elapsed_ms"] for t in traces) / 1000,
        "api_cost_usd": sum(costs) if all(cost is not None for cost in costs) else None,
    }
    write_json(args.output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
