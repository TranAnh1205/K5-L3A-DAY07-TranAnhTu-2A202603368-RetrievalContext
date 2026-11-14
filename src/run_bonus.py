"""Run the separate bonus benchmark without sending gold to the agent."""

import argparse
import hashlib
import json
from pathlib import Path

from src.bonus_agent import BonusAgent


BENCHMARK_SHA256 = "2e8efa369fb6a79b6d27e049ffc162532adff0fe7db49f763f1ae329118a0853"
MODES = {
    "text": {"use_vision": False, "anchor_routing": False, "top_k": 3},
    "vision": {"use_vision": True, "anchor_routing": False, "top_k": 3},
    "vision_anchor": {"use_vision": True, "anchor_routing": True, "top_k": 3},
    "vision_anchor_verify": {"use_vision": True, "anchor_routing": True,
                             "verify_answer": True, "top_k": 3},
    "vision_anchor_repair": {"use_vision": True, "anchor_routing": True,
                             "citation_repair": True, "top_k": 3},
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--mode", choices=tuple(MODES), required=True)
    parser.add_argument("--benchmark", type=Path, default=Path("data/advanced/benchmark.json"))
    parser.add_argument("--index", type=Path, default=Path("data/advanced/page_index.json"))
    parser.add_argument("--pdf", type=Path, default=Path("data/advanced/source_100pages.pdf"))
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if hashlib.sha256(args.benchmark.read_bytes()).hexdigest() != BENCHMARK_SHA256:
        raise ValueError("Bonus benchmark changed after freeze")
    if args.split == "test":
        config = json.loads(Path("report/bonus/selected_config.json").read_text(encoding="utf-8"))
        if config.get("mode") != args.mode or config.get("model") != args.model:
            raise ValueError("Test mode/model differs from frozen dev selection")
        if config.get("benchmark_sha256") != BENCHMARK_SHA256:
            raise ValueError("Frozen benchmark hash differs")
        protected = {"pdf_sha256": args.pdf, "index_sha256": args.index,
                     "visual_transcriptions_sha256": args.index.parent / "visual_transcriptions.json",
                     "agent_code_sha256": Path("src/bonus_agent.py"),
                     "runner_code_sha256": Path("src/run_bonus.py")}
        for key, path in protected.items():
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != config.get(key):
                raise ValueError(f"Test input/code differs from frozen dev selection: {key}")
    cases = [q for q in json.loads(args.benchmark.read_text(encoding="utf-8")) if q["split"] == args.split]
    args.output.mkdir(parents=True, exist_ok=True)
    traces_path = args.output / "traces.json"
    if traces_path.exists():
        traces = json.loads(traces_path.read_text(encoding="utf-8"))
        if any(t.get("mode") != args.mode or t.get("split") != args.split for t in traces):
            raise ValueError("Output already contains another configuration")
    else:
        traces = []
    done = {t["query_id"] for t in traces}
    agent = BonusAgent(index_path=args.index, pdf_path=args.pdf, model=args.model, **MODES[args.mode])
    try:
        for q in cases:
            if q["id"] in done:
                continue
            trace = agent.run(q["question"])
            trace.update(query_id=q["id"], split=args.split, category=q["category"], mode=args.mode)
            traces.append(trace)
            traces_path.write_text(json.dumps(traces, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            print(q["id"], trace["status"], trace.get("answer"), flush=True)
    finally:
        agent.close()
    summary = {"split": args.split, "mode": args.mode, "model": args.model,
               "cases": len(cases), "traces": len(traces),
               "status_counts": {status: sum(t["status"] == status for t in traces)
                                 for status in ("answered", "abstain", "error")},
               "total_elapsed_seconds": sum(t["elapsed_ms"] for t in traces)/1000,
               "estimated_api_cost_usd": sum(t.get("api_cost_usd") or 0 for t in traces),
               "missing_usage_cases": sum(t.get("api_cost_usd") is None for t in traces)}
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
