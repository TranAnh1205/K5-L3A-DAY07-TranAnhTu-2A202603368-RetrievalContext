# Day 07 code

`day6_retriever.py` connects to the real Day 06 local Qdrant store. It uses the same `BAAI/bge-small-en-v1.5` query model and the `day06_fixed_a` collection, chosen from the Day 06 development benchmark. The `search` method returns `id`, `text`, `source_id`, `source`, `page`, `metadata`, and `score` for the Day 07 agent contract.

From the Day 07 repository root, install dependencies with `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. The following commands follow section 3 of `starter/README.md`: export Day 06 chunks/questions, use the provided converter, then run the provided TF-IDF baseline on dev only.

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m src.day6_retriever --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion'
.\.venv\Scripts\python.exe -m src.export_day6 --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --output starter\data\day6_raw
.\.venv\Scripts\python.exe starter\convert_day6.py --chunks starter\data\day6_raw\chunks.json --questions starter\data\day6_raw\questions.json --output starter\data\converted
.\.venv\Scripts\python.exe starter\baseline.py --chunks starter\data\converted\chunks.json --questions starter\data\converted\questions.json --split dev --output starter\results\day6-dev-tfidf-smoke
```

The export contains 484 real A chunks and all 20 frozen Day 06 questions. The TF-IDF dev smoke run returned Hit@1 8/15 and Evidence Hit@3 12/15. This smoke run is separate from the Day 07 benchmark in `data/questions.json`. `starter/data/` and `starter/results/` are generated local artifacts ignored by Git; regenerate them with these commands.

Compare the three retrieval methods on the fixed Day 07 **dev** split:

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe data\validate_questions.py
.\.venv\Scripts\python.exe -m src.retrieval_benchmark --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --split dev --output starter\results\day7-retrieval-dev
```

The script runs TF-IDF, dense retrieval from Qdrant, and reciprocal-rank-fusion hybrid on the same 484 chunks and 17 dev questions. It applies the question's `section` filter before ranking, passes only question text and filter to retrievers, and excludes the two no-evidence cases from Hit@1, Evidence Hit@3, and Context Evidence Rate denominators. It writes per-query rankings and context plus a summary. The checked-in dev run is in `report/retrieval_dev/` and described in `report/retrieval_dev.md`. The later held-out test evaluation is in `report/retrieval_test/` and `report/agent_test/`, documented in `report/agent_test.md`.

## Real model agent

`real_agent.py` connects the provided `starter/agentic.py` loop to an OpenAI-compatible Chat Completions endpoint. It uses a real model to choose `search` or `answer`; the search tool can use dense, TF-IDF or hybrid retrieval. For OpenAI API, the default model is [`gpt-5.4-mini`](https://developers.openai.com/api/docs/models/gpt-5.4-mini), which supports Chat Completions. Set `OPENAI_API_KEY` in your local environment. Override the model with `AGENT_MODEL` or `--model`, and set `AGENT_BASE_URL` for a different provider. Do not commit keys or `.env` files.

For one answerable smoke run from the Day 07 repository root:

```powershell
$env:PYTHONUTF8 = '1'
$env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'User')
if (-not $env:OPENAI_API_KEY) { throw 'Set OPENAI_API_KEY in the Windows User environment first.' }
.\.venv\Scripts\python.exe -m src.real_agent --question 'What labor shift helped reduce both poverty and inequality in Viet Nam from 2010 to 2014?' --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --method dense --output starter\results\agent-d01.json
```

The default limits are 2 searches, 3 results per search and 4,000 characters of cumulative context. The model can search again when the first context is insufficient. Output includes every model action, search query and result, packed context, answer, citation IDs, timing, token usage when returned by the provider, and errors. Citation IDs are checked against context by the starter loop; their semantic support still requires human review. For the default model, API cost is estimated from returned token usage using the model card prices checked on 2026-11-14; other models or missing usage yield `null`. If a model or endpoint fails, the run records `status: error`; it does not substitute a mock result. This single-question command is a smoke run, not the required dev/test agent evaluation.

Two real-model dev smoke cases, one answerable and one no-evidence, are reviewed in `report/agent_smoke.md` with complete traces in `report/agent_smoke/`.

To reproduce the three **dev-only** agent runs, first load `OPENAI_API_KEY` from the Windows User environment as above, then run:

```powershell
.\.venv\Scripts\python.exe -m src.run_agent_dev --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --method dense --output starter\results\agent_dev_dense
.\.venv\Scripts\python.exe -m src.run_agent_dev --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --method hybrid_rrf --output starter\results\agent_dev_hybrid
.\.venv\Scripts\python.exe -m src.run_agent_dev --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --method hybrid_rrf --citation-retries 1 --output starter\results\agent_dev_hybrid_repair
```

These runs use top-3, two search turns and a 4,000-character context budget unless overridden. `src.run_agent_dev` accepts only the fixed dev split and writes traces incrementally. The checked-in results and source-reviewed labels are in `report/agent_dev/`; the comparison and error analysis are in `report/agent_dev.md`. The selected configuration is frozen in `report/agent_dev/selected_config.json` before test evaluation.

The Day 06 PDF and `starter/qdrant_storage` are local generated artifacts. To reproduce them on another machine, follow the setup commands in the [Day 06 submission](https://github.com/TranAnh1205/K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion/tree/day06-submission). Do not run two processes against the same Qdrant local store at once.

## Locked held-out test

After `report/agent_dev/selected_config.json` was frozen on dev, the test runner evaluated **only** the dense baseline and the selected Hybrid RRF on all seven Day 7 test cases. Its hash checks guard against using a changed question set or Day 6 chunk export. `--role selected` reads the frozen method, limits and model; no test-driven tuning is part of this workflow. Load `OPENAI_API_KEY` as above, then from the repo root:

```powershell
.\.venv\Scripts\python.exe -m src.retrieval_benchmark --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --split test --methods dense hybrid_rrf --budget-chars 2400 --output starter\results\retrieval_test_locked
.\.venv\Scripts\python.exe -m src.run_agent_test --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --role baseline --output starter\results\agent_test_baseline
.\.venv\Scripts\python.exe -m src.run_agent_test --day6-repo 'E:\Hoanthanhbailapngay06\K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion' --role selected --output starter\results\agent_test_selected
```

`report/agent_test.md` reports the committed test runs and PDF-reviewed labels; `report/individual/202603368_TranAnhTu.md` is the filled personal report. Rerunning the model can produce different answers and API charges.

## Separate 100-page advanced challenge

The source, rights, packet-page mapping, index inventory and fixed 18/30 dev/test benchmark are in [`data/advanced/README.md`](../data/advanced/README.md). The PDF packet and page index are committed. The bonus pipeline uses `pymupdf` to render original pages on demand, TF-IDF to search all 100 pages, caption-anchor routing from the question, and `gpt-5.4-mini` for search planning, vision answering and optional missing-citation repair. `report/bonus/selected_config.json` freezes the dev-selected mode and hashes before test; `report/bonus_report.md` records the full outcome. From the repository root:

```powershell
.\.venv\Scripts\python.exe -m src.bonus_index
.\.venv\Scripts\python.exe data\advanced\validate_benchmark.py
$env:OPENAI_API_KEY = [Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'User')
.\.venv\Scripts\python.exe -m src.run_bonus --split dev --mode vision_anchor_repair --output starter\results\bonus_dev_replay
.\.venv\Scripts\python.exe -m src.run_bonus --split test --mode vision_anchor_repair --output starter\results\bonus_test_replay
```

The test command verifies frozen benchmark/PDF/index/visual-note/code hashes. A rerun is a fresh paid model run and may differ from the committed result.
