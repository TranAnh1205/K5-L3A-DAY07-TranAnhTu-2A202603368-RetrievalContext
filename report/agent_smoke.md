# Real-model agent smoke check (dev only)

Ran the `src.real_agent` CLI with OpenAI API model `gpt-5.4-mini`, the Day 6 Qdrant A collection, dense search, at most 2 searches, top-3 results per search, and a 4,000-character context budget. The model saw only each question and retrieved context, never benchmark gold or expected behavior. The [model card](https://developers.openai.com/api/docs/models/gpt-5.4-mini) is the source of the estimated API prices used by the code on 2026-11-14. These are two **dev smoke cases**, not the required full dev or test evaluation.

| Case | Outcome | Searches / model calls | Final context | Total tokens | API cost estimate | Elapsed |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `d01`, answerable | Answered with one citation | 1 / 2 | 1,964 chars | 1,077 | $0.00122025 | 5.89 s |
| `d16`, no evidence | Abstained | 2 / 3 | 3,277 chars | 2,415 | $0.00217875 | 4.03 s |

For `d01`, the model answered that labor shifted from agriculture into manufacturing and services jobs. Its cited chunk `dae9b91eb9df9e71d469e44fb5b4dae4` is in the final context, has the World Bank report source and physical PDF page 11, and explicitly states that shift. I manually checked the cited text against the answer; the citation supports the claim.

For `d16`, the model made two searches for an *observed* 2025 urban housing area and returned “Không đủ bằng chứng để trả lời.” with no citation. The corpus review in `data/BENCHMARK_PROTOCOL.md` found a 2025 **target**, but no observed 2025 outcome. The abstention is correct for this question. The two search result sets did not include the target page, so this case should not be interpreted as proving absence from top-k alone.

Full [answerable trace](agent_smoke/agent-d01.json) and [no-evidence trace](agent_smoke/agent-d16.json) preserve model actions, usage, search queries, ranked chunks, source/page/metadata, context, final response, citation IDs, elapsed time and estimated API cost. API credentials are not stored. Error handling and protocol shape were checked by tests; neither smoke case experienced a provider or vector-store error.

Next evaluation work: run the agent on the whole dev split for the configurations under comparison, label answer support and citation support manually, perform two improvement trials, then freeze the selected configuration before touching the Day 7 test split.
