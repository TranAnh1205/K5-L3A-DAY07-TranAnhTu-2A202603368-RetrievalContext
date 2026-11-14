"""Inventory every page of the 100-page OpenStax study packet.

The PDF stays authoritative. Text and caption records point back to its
physical packet page and the corresponding original-book page.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf


CAPTION = re.compile(r"\b(?:Exhibit|Table)\s+\d+\.\d+\b", re.I)


def build(pdf_path: Path) -> dict:
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    doc = pymupdf.open(pdf_path)
    if len(doc) != 100:
        raise ValueError(f"Bonus packet needs exactly 100 pages; got {len(doc)}")
    pages = []
    for index, page in enumerate(doc):
        text = page.get_text("text", sort=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        captions = []
        by_label = {}
        for line in lines:
            for match in CAPTION.finditer(line):
                key = match.group(0).lower()
                boxes = page.search_for(match.group(0))
                follows = line[match.end():].strip().split(maxsplit=1)
                next_word = follows[0].lower().strip(".,:;") if follows else ""
                item = {"label": match.group(0), "line": line[:300],
                        "is_caption": line.lower().startswith(key)
                        and next_word not in {"shows", "show", "illustrates", "provides", "offers", "is", "was", "are"},
                        "bbox": list(boxes[-1]) if boxes else None}
                if key not in by_label or (item["is_caption"] and not by_label[key]["is_caption"]):
                    by_label[key] = item
        captions = list(by_label.values())
        pages.append({"id": f"bonus-p{index+1:03}", "page": index+1,
                      "original_page": index+89, "source_id": "openstax-management-study100",
                      "source": "https://openstax.org/details/books/principles-management",
                      "text": text, "characters": len(text),
                      "image_count": len(page.get_images(full=True)),
                      "drawing_count": len(page.get_drawings()),
                      "captions": captions,
                      "image_locator": {"pdf_page": index+1,
                                        "bbox": [0, 0, page.rect.width, page.rect.height]}})
    return {"source_pdf": str(pdf_path), "sha256": digest, "pages": pages,
            "page_count": len(pages),
            "text_pages": sum(bool(p["text"].strip()) for p in pages),
            "caption_count": sum(len(p["captions"]) for p in pages),
            "image_pages": sum(p["image_count"] > 0 for p in pages),
            "drawing_pages": sum(p["drawing_count"] > 0 for p in pages)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=Path("data/advanced/source_100pages.pdf"))
    parser.add_argument("--output", type=Path, default=Path("data/advanced/page_index.json"))
    args = parser.parse_args()
    result = build(args.pdf)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "pages"}, indent=2))


if __name__ == "__main__":
    main()
