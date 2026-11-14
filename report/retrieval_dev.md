# Day 7 retrieval comparison: dev only

Run on the frozen `data/questions.json` dev split: 15 answerable questions and 2 no-evidence questions. Corpus: 484 chunks from the Day 6 A collection (`day06_fixed_a`), 67 selected pages of the World Bank 2024 Viet Nam poverty and equity report. Dense query embedding: `BAAI/bge-small-en-v1.5`, 384 dimensions, cosine Qdrant index. The three methods use the original question text and the user-supplied `section` filter when present; no answer or gold evidence is passed to a retriever.

TF-IDF uses word tokens and cosine similarity. Dense queries the existing Day 6 Qdrant index. Hybrid gets 20 candidates from each, fuses their ranks with reciprocal rank fusion (`1/(60+rank)`), and returns the top 3. This avoids adding incomparable cosine and TF-IDF scores. A context packer keeps complete ranked chunks, their IDs, source and page under a 2,400-character budget. All 3 top-ranked chunks fit in every dev context for this run. Index construction took 0.081 s for the local TF-IDF index; Qdrant and embedding initialization are not included in per-query latency. No paid API was called; API cost was $0. Local CPU and storage costs are not monetized.

| Method | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Median query time | Mean candidate count |
| --- | ---: | ---: | ---: | ---: | ---: |
| TF-IDF | 8/15 (53.3%) | 12/15 (80.0%) | 12/15 (80.0%) | 5.8 ms | 3.0 |
| Dense Qdrant | 8/15 (53.3%) | 12/15 (80.0%) | 12/15 (80.0%) | 21.3 ms | 3.0 |
| Hybrid RRF | 9/15 (60.0%) | 12/15 (80.0%) | 12/15 (80.0%) | 42.3 ms | 32.6 unique |

Hit means a top-ranked chunk contains the complete recorded evidence span and has the correct source ID and physical PDF page. The two no-evidence questions were searched and traced, but excluded from all three denominators. A retrieved page by itself is not a hit if its chunk lacks the evidence span. Context Evidence Rate here equals Hit@3 because every top-3 chunk fit the context. This measures evidence presence, not answer quality or whether an agent would correctly abstain.

Dev errors show different strengths and limits. For `d02`, dense found the evidence at rank 2, while TF-IDF and hybrid missed the complete span in their top 3. For `d09`, TF-IDF found it at rank 1, while dense and hybrid missed it. All three missed `d12`, despite applying its Part 2 filter, so this is a retrieval issue to investigate in the next improvement trials. `d07` is found by dense and hybrid but not TF-IDF. These examples explain why hybrid's one extra Hit@1 does not improve Evidence Hit@3.

The full [TF-IDF](retrieval_dev/tfidf_traces.json), [dense](retrieval_dev/dense_traces.json), and [hybrid](retrieval_dev/hybrid_rrf_traces.json) traces contain every question, filter, ranked chunk with score and source/page/metadata, packed context, hit flags and elapsed time. [Summary JSON](retrieval_dev/summary.json) contains the numeric aggregates. Results are from this single local run; latency varies by machine and cache. The configuration has not been finalized for test, and no Day 7 test run is included here. Agent calls, answer labels and citation review remain separate work.
