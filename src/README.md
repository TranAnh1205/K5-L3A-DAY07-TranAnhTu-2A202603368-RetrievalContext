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

The export contains 484 real A chunks and all 20 frozen Day 06 questions. The TF-IDF dev smoke run returned Hit@1 8/15 and Evidence Hit@3 12/15. This is **not** the completed Day 07 benchmark: the required unanswerable cases and fresh test set have not been created, and no Day 07 test run has occurred. `starter/data/` and `starter/results/` are generated local artifacts ignored by Git; regenerate them with these commands.

The Day 06 PDF and `starter/qdrant_storage` are local generated artifacts. To reproduce them on another machine, follow the setup commands in the [Day 06 submission](https://github.com/TranAnh1205/K5-L3A-DAY06-TranAnhTu-202603368-DataIngestion/tree/day06-submission). Do not run two processes against the same Qdrant local store at once.
