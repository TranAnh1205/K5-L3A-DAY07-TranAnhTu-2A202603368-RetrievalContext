# Day 7 benchmark protocol

## Source and fixed split

The source is World Bank (2024), *Viet Nam bi-annual poverty & equity update - June 2024: Towards more inclusive cities* (CC BY 3.0 IGO). The Day 6 manifest records the [PDF source](https://documents1.worldbank.org/curated/en/099070224032598476/pdf/P1810941a2c34a0491b71e1f532b48e129f.pdf), snapshot SHA-256 `5e95b6bcb352fe002e9d4447c6a1e0936a841777e320e5b8e344856829c85ec4`, and 67 included physical PDF pages out of 92. The Day 7 corpus is the exported Day 6 chunk set in `starter/data/converted/chunks.json`. In this benchmark, `page` is the physical PDF page number.

`data/questions.json` is the fixed benchmark (SHA-256 `3bb60bee86dc22e974cf074b9bb9d1abbc83f1f2ce28dbc38d089b5546be28ab`). It contains 15 answerable dev questions converted from the Day 6 **dev** split, two new no-evidence dev questions, five new answerable test questions, and two new no-evidence test questions. The old Day 6 test questions were inspected during Day 6 work, so none are reused as Day 7 test. The new answerable test items use physical pages 28, 61, 69, 76, and 85, none of which was a Day 6 gold page. Some questions supply a `section` filter in the wording and in `filter`.

## Evidence review

For each answerable question, `gold` lists the source ID, physical page, and a literal evidence span. Each span was checked against the source PDF text and programmatically checked to occur in one exported chunk with the same source and page. The filter, when present, admits that chunk. The current questions need one evidence span each; there are no multi-hop items. A retrieval hit requires an eligible chunk containing the complete gold span, with the matching source and page. Equivalent supporting spans may be accepted only after a documented manual review; add them to `gold` before calculating final metrics. No-evidence questions are excluded from Hit@1 and Evidence Hit@3 denominators.

**Dev audit note, 2026-11-14:** An equivalent span for `d12` on physical page 65 was discovered after the benchmark freeze during dev trace review. It is documented in `report/agent_dev/gold_alternatives_reviewed.json` and accepted only for the separately reviewed context/answer/citation labels. It was not added retroactively to the frozen `gold` array; original-query automatic Hit@ metrics retain the original strict definition and hash. A future benchmark revision would add the span to `gold` and rerun every compared configuration before reporting revised automatic metrics. No test case was used for this audit.

The no-evidence questions were checked against all 67 indexed pages, including the relevant sections:

| ID | Review of the corpus |
| --- | --- |
| d16 | The 2025 housing area mentions on pages 75, 77, and 81 are **targets**, not a measured 2025 outcome. The other 2025 mention on page 37 concerns agriculture. |
| d17 | The only computer ownership mention, on page 69, gives a qualitative and spatial comparison, not a citywide percentage. |
| t11 | Flood coverage on pages 75–81 discusses exposure and modeled depth; no HCMC flood death count for 2022 appears. The corpus has no `fatality` mention; the `death` mention on page 60 concerns population growth. |
| t12 | Renting appears on pages 46, 77, and 86 and migrants on pages 82–84, but no median monthly rent paid by HCMC migrants in 2019 appears. |

This is a review of the **indexed corpus**, not a claim about all external sources. A failure to retrieve a top-k result was not used as proof of absence. The review is recorded here so a human can recheck the PDF before submission.

## Evaluation rule

Use dev only while building and comparing retrieval and agent configurations. Freeze the benchmark and the configuration selection rule before the first Day 7 test evaluation. Select the configuration with the highest dev Evidence Hit@3; break ties by dev Context Evidence Rate, then lower measured query latency. Record the chosen configuration, index/corpus version, context budget, model, parameters, and selection result in the report before running the Day 7 test. If test answers or labels are used for tuning, create a fresh independent test set.

At query time, pass only the question text and its user-supplied `filter` to retrieval/agent code. Keep `gold`, `expected_answer`, `answerable`, `expected_behavior`, and `absence_reason` in the evaluator. For no-evidence cases, the expected agent behavior is to search and then abstain. Record retrieval ranking, final context, agent traces, citations, and manual labels as specified in the repository's `BENCHMARK.md`. This section records the protocol set before evaluation. The later held-out test results and manual labels are documented in `report/agent_test.md`; the fixed benchmark JSON was not changed.

Run `python data/validate_questions.py --chunks starter/data/converted/chunks.json` from the repository root to check split counts, schema, evidence containment, and filters. This validator does not establish absence of evidence; use the review above and inspect the PDF.
