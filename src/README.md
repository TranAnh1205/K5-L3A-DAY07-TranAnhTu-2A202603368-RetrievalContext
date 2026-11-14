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

The script runs TF-IDF, dense retrieval from Qdrant, and reciprocal-rank-fusion hybrid on the same 484 chunks and 17 dev questions. It applies the question's `section` filter before ranking, passes only question text and filter to retrievers, and excludes the two no-evidence cases from Hit@1, Evidence Hit@3, and Context Evidence Rate denominators. It writes per-query rankings and context plus a summary. The checked-in dev run is in `report/retrieval_dev/` and described in `report/retrieval_dev.md`. No Day 07 test evaluation has been run.

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

The Day 06 PDF and `starter/qdrant_storage` are local generated artifacts. To reproduce them on another machine, follow the setup commands in the [Day 06 submission](https://github.com/TranAnh1205/K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion/tree/day06-submission). Do not run two processes against the same Qdrant local store at once.
