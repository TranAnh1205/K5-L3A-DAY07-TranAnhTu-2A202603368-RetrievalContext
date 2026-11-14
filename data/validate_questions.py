"""Check the Day 7 benchmark against the exported Day 6 corpus."""

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=Path("data/questions.json"))
    parser.add_argument("--chunks", type=Path, default=Path("starter/data/converted/chunks.json"))
    args = parser.parse_args()
    questions = json.loads(args.questions.read_text(encoding="utf-8"))
    chunks = json.loads(args.chunks.read_text(encoding="utf-8"))
    assert isinstance(questions, list) and isinstance(chunks, list)

    counts = Counter()
    ids = set()
    normalized_questions = set()
    for question in questions:
        qid = question["id"]
        split = question["split"]
        assert qid not in ids, f"Duplicate ID: {qid}"
        assert split in {"dev", "test"}, qid
        ids.add(qid)
        normalized = " ".join(question["question"].lower().split())
        assert normalized not in normalized_questions, f"Duplicate question: {qid}"
        normalized_questions.add(normalized)
        assert normalized, qid

        if question.get("answerable") is False:
            counts[(split, "no_evidence")] += 1
            assert question["expected_behavior"] == "search_and_abstain", qid
            assert question["absence_reason"].strip(), qid
            assert "gold" not in question and "expected_answer" not in question, qid
            continue

        counts[(split, "answerable")] += 1
        assert question["expected_answer"].strip(), qid
        assert question["gold"], qid
        for gold in question["gold"]:
            matches = [chunk for chunk in chunks
                       if chunk["source_id"] == gold["source_id"]
                       and chunk["page"] == gold["page"]
                       and gold["evidence"] in chunk["text"]]
            assert matches, f"Evidence not contained in one source/page chunk: {qid}"
            if "filter" in question:
                assert any(all(chunk["metadata"].get(key) == value
                               for key, value in question["filter"].items())
                           for chunk in matches), f"Filter excludes evidence: {qid}"

    for key, minimum in {("dev", "answerable"): 15,
                         ("dev", "no_evidence"): 2,
                         ("test", "answerable"): 5,
                         ("test", "no_evidence"): 2}.items():
        assert counts[key] >= minimum, f"Need {minimum} for {key}: got {counts[key]}"
    print(f"PASS: {len(questions)} questions; "
          f"dev {counts['dev', 'answerable']} answerable + {counts['dev', 'no_evidence']} no-evidence; "
          f"test {counts['test', 'answerable']} answerable + {counts['test', 'no_evidence']} no-evidence")
    print("Every answerable evidence span occurs within one matching source/page chunk; filters admit it.")
    print("No-evidence claims still require document review; this script cannot prove absence.")


if __name__ == "__main__":
    main()
