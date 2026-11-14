"""Run the real agent on the fixed Day 7 dev split and preserve each trace."""

import argparse
import json
import os
import time
from pathlib import Path

from starter.agentic import run_agent
from src.real_agent import ChatController, SearchTool, DEFAULT_MODEL, estimate_api_cost


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all Day 7 dev cases with a real model")
    parser.add_argument("--day6-repo", required=True, type=Path)
    parser.add_argument("--questions", type=Path, default=Path("data/questions.json"))
    parser.add_argument("--chunks", type=Path, default=Path("starter/data/converted/chunks.json"))
    parser.add_argument("--method", choices=("dense", "tfidf", "hybrid_rrf"), default="dense")
    parser.add_argument("--model", default=os.environ.get("AGENT_MODEL") or DEFAULT_MODEL)
    parser.add_argument("--base-url", default=os.environ.get("AGENT_BASE_URL") or "https://api.openai.com/v1")
    parser.add_argument("--max-searches", type=int, default=2)
    parser.add_argument("--citation-retries", type=int, default=0)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--budget-chars", type=int, default=4000)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    questions = [q for q in json.loads(args.questions.read_text(encoding="utf-8"))
                 if q["split"] == "dev"]
    if len(questions) != 17:
        parser.error("Expected the frozen 17-case dev split")
    if args.max_searches < 1 or args.citation_retries < 0 or args.top_k < 1 or args.budget_chars < 1:
        parser.error("Search and context limits must be positive")
    controller_config = {"base_url": args.base_url, "model": args.model,
                         "api_key": os.environ.get("OPENAI_API_KEY"), "timeout_seconds": 120}
    traces: list[dict] = []
    retriever = SearchTool(method=args.method, day6_repo=args.day6_repo,
                           chunks_path=args.chunks)
    try:
        for question in questions:
            controller = ChatController(**controller_config)
            filters = question.get("filter")
            started = time.perf_counter()
            try:
                # Gold and expected behavior are intentionally not passed to the agent.
                result = run_agent(
                    question["question"], controller, retriever,
                    filters=filters, max_searches=args.max_searches,
                    top_k=args.top_k, budget=args.budget_chars,
                    max_citation_repairs=args.citation_retries,
                )
            except Exception as error:
                result = {"status": "error", "answer": "", "citations": [],
                          "events": retriever.calls,
                          "error": f"{type(error).__name__}: {error}"}
            trace = {
                "query_id": question["id"], "split": "dev", "question": question["question"],
                "filter": filters, "model": args.model, "method": args.method,
                "max_searches": args.max_searches, "top_k": args.top_k,
                "citation_retries": args.citation_retries,
                "budget_chars": args.budget_chars,
                "model_calls": controller.calls,
                "tool_calls": retriever.calls,
                "elapsed_ms": (time.perf_counter() - started) * 1000,
                "api_cost_usd": estimate_api_cost(args.model, controller.calls),
                **result,
            }
            traces.append(trace)
            # Incremental write preserves completed cases if a later call fails.
            write_json(args.output / "traces.json", traces)
            print(f"{question['id']} {trace['status']} searches={len(trace['tool_calls'])} "
                  f"cost={trace['api_cost_usd']}", flush=True)
            retriever.calls = []
    finally:
        retriever.close()
    costs = [trace["api_cost_usd"] for trace in traces]
    summary = {
        "split": "dev", "method": args.method, "model": args.model,
        "top_k": args.top_k, "max_searches": args.max_searches,
        "citation_retries": args.citation_retries,
        "budget_chars": args.budget_chars, "cases": len(traces),
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
