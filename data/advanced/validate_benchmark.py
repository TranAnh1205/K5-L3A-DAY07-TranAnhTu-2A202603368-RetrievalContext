"""Validate the fixed bonus split and source locators; does not judge answers."""

import hashlib
import json
from collections import Counter
from pathlib import Path


EXPECTED_SHA256 = "2e8efa369fb6a79b6d27e049ffc162532adff0fe7db49f763f1ae329118a0853"


def main() -> None:
    root = Path(__file__).parent
    benchmark = root / "benchmark.json"
    digest = hashlib.sha256(benchmark.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Bonus benchmark hash differs from pretrial freeze")
    cases = json.loads(benchmark.read_text(encoding="utf-8"))
    index = json.loads((root / "page_index.json").read_text(encoding="utf-8"))
    if len(index["pages"]) != 100 or any(page["page"] != i for i, page in enumerate(index["pages"], 1)):
        raise ValueError("Source packet page inventory incomplete")
    if len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Duplicate benchmark IDs")
    counts = Counter((case["split"], case["category"]) for case in cases)
    required = {("dev", "table"): 3, ("dev", "image"): 3, ("dev", "chart"): 3,
                ("dev", "multi_hop"): 3, ("dev", "text"): 3, ("dev", "unanswerable"): 3,
                ("test", "table"): 6, ("test", "image"): 5, ("test", "chart"): 5,
                ("test", "multi_hop"): 4, ("test", "text"): 4, ("test", "unanswerable"): 6}
    if counts != required:
        raise ValueError(f"Bonus split/categories invalid: {counts}")
    for case in cases:
        if case["answerable"]:
            if not case.get("expected_answer") or not case.get("evidence"):
                raise ValueError(f"{case['id']}: missing answer/evidence")
            if case["category"] == "multi_hop" and len(case["evidence"]) < 2:
                raise ValueError(f"{case['id']}: multi-hop needs two sources")
            for ev in case["evidence"]:
                page = ev["page"]
                if not 1 <= page <= 100 or ev["original_book_page"] != page + 88:
                    raise ValueError(f"{case['id']}: invalid page mapping")
                if not ev.get("detail") or not ev.get("locator"):
                    raise ValueError(f"{case['id']}: missing locator/detail")
                label = ev["locator"].split(";")[0]
                if label.startswith(("Exhibit", "Table")):
                    if ev.get("region_bbox_pdf") is None:
                        raise ValueError(f"{case['id']}: missing visual bbox")
                    page_text = index["pages"][page-1]["text"]
                    if label not in page_text:
                        raise ValueError(f"{case['id']}: label not on cited PDF page")
        elif not case.get("absence_review"):
            raise ValueError(f"{case['id']}: missing corpus absence review")
    print(f"PASS: {len(cases)} bonus cases, dev=18, test=30; 100 indexed pages; SHA-256 {digest}")


if __name__ == "__main__":
    main()
