# Day 7 held-out test: locked baseline and selected Hybrid RRF

The benchmark and dev selection were fixed before these test runs. `report/agent_dev/selected_config.json` freezes the selected Hybrid RRF (top-3, at most two searches, 4,000 context characters, zero citation retries), model `gpt-5.4-mini`, and hashes of the 24-case benchmark and 484-chunk export. The dense baseline uses the same model and agent limits. Test was run once per configuration; no configuration changed afterward. Test contains five answerable items (`t06`–`t10`) and two no-evidence items (`t11`–`t12`).

## Retrieval on the original question

This local comparison uses the original question and its user-supplied filter, top-3 results and a 2,400-character context budget. All rates below exclude the two no-evidence cases. Hit@1 and Evidence Hit@3 require the complete *frozen* gold span in a chunk with the specified source and physical PDF page. A full gold span in the packed context is required for automatic Context Evidence Rate.

| Method | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Median query time | API cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Dense Qdrant baseline | 1/5 | 2/5 | 2/5 | 16.48 ms | $0 |
| Selected Hybrid RRF | 1/5 | 3/5 | 3/5 | 28.42 ms | $0 |

See [`report/retrieval_test/summary.json`](retrieval_test/summary.json) and both per-query trace files in that directory. Retrieval latency excludes one-time embedding/index initialization and local compute expense.

## Real agent and source review

Each run searched on all 7 questions, used 7 tool calls and 14 model calls, and had no provider or vector-store error. The agent may reformulate a search, so the final context/answer labels below are separate from the original-query retrieval scores. Every answered response included a citation ID. All 14 traces were read and the relevant PDF pages were checked. The per-case reasons and source pages are recorded for independent confirmation.

| Configuration | Grounded answer 0/1/2 (5) | Mean /2 | Valid citations | Answer citation coverage | Correct abstention | False abstention | Time | API cost estimate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense baseline | 1 / 2 / 2 | 1.20 | 3/4 | 4/4 | 2/2 | 1/5 | 17.75 s | $0.008079 |
| Selected Hybrid RRF | 0 / 2 / 3 | 1.60 | 3/5 | 5/5 | 2/2 | 0/5 | 14.43 s | $0.008221 |

Grade 2 requires a correct answer with enough source support, grade 1 means partially correct or incompletely supported, and grade 0 is wrong, unsupported or a false refusal. Citation validity checks whether the **cited chunk** supports the whole material claim; an ID merely occurring in context is insufficient. Context grade 2 means the final packed context supplies all needed evidence; grade 1 means only a partial clue; grade 0 means no relevant support.

| ID | Source PDF fact / behavior | Dense: context, answer, citation | Hybrid: context, answer, citation | Review finding |
| --- | --- | --- | --- | --- |
| `t06` | Page 28: prosperity gap 2.6 | 0, 0, no citation | 2, 2, valid | Dense falsely refused; Hybrid found the exact span. |
| `t07` | Page 61: wards **and district towns**; Part 2 filter | 1, 1, invalid | 2, 1, invalid | Dense answered both but cited a truncated ward-only table. Hybrid had page 60's full support in context yet omitted district towns and cited that same truncated table. |
| `t08` | Page 69: small-area estimates reach **24 districts** | 1, 1, valid for partial statement | 1, 1, invalid for full statement | Dense omitted 24. Hybrid gave 24 using page 70, which verifies district count but does not tie the number to small-area estimation. |
| `t09` | Page 76: **10,045 schools** | 2, 2, valid | 2, 2, valid | Both correctly answered and cited. |
| `t10` | Page 85: about **1,400 HCMC households** | 2, 2, valid | 2, 2, valid | Both cited an equivalent explicit passage on page 68; Hybrid also retrieved frozen gold page 85. |
| `t11` | No 2022 HCMC flood-death count in indexed corpus | searched, correct refusal | searched, correct refusal | No invented mortality statistic. |
| `t12` | No 2019 HCMC migrant median rent in indexed corpus | searched, correct refusal | searched, correct refusal | No invented rental statistic. |

For `t10`, the frozen gold page is 85, but physical page 68 states the same 1,400 figure. The equivalent evidence is recorded in [`gold_alternatives_reviewed.json`](agent_test/gold_alternatives_reviewed.json) and credited only in the manually reviewed labels. The fixed benchmark and automatic retrieval scores were not revised after seeing test.

The two no-evidence decisions rest on the corpus-level check recorded in [`data/BENCHMARK_PROTOCOL.md`](../data/BENCHMARK_PROTOCOL.md), not on empty top-k results. The [`reviews.json`](agent_test/selected/reviews.json) and [`metrics.json`](agent_test/selected/metrics.json) for Hybrid, with corresponding baseline files, contain each label and aggregate. Full [`traces.json`](agent_test/selected/traces.json) records each query, filter, ranked tool result, packed context, answer, citation, usage, time, cost and status. This single seven-case test does not establish stable improvement beyond this benchmark.

## Reproduce

From the repo root, first rebuild/export the Day 6 index as described in [`src/README.md`](../src/README.md) and set `OPENAI_API_KEY` in your environment. Then:

```powershell
cd starter
..\.venv\Scripts\python.exe -m src.retrieval_benchmark --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --split test --methods dense hybrid_rrf --budget-chars 2400 --output results/retrieval_test_locked
..\.venv\Scripts\python.exe -m src.run_agent_test --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --role baseline --output results/agent_test_baseline
..\.venv\Scripts\python.exe -m src.run_agent_test --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --role selected --output results/agent_test_selected
```

The displayed runs were already made and their results committed under `report/`; rerunning the real model may vary and incurs API cost.
