# Prompt tuning · round gemini · 2026-09-26 · gemini-3.8-flash arm A · sample assist_100 (`ab72e89ace15`, test split, 1 conversations)

Each row is the same call points with the guideline library rendered at a different length. Deltas are paired against `full` point by point, in percentage points with a 95% interval. Cost per 1,000 conversations = mean cost per turn x 13.10 x 1,000.

| Library | Next action | Δ next action vs full | Intent | Δ intent vs full | Cache reads / turn | Uncached input / turn | Output / turn | p50 / p95 latency | Cost / 1,000 conversations | Cut vs full | Gates (quality · cost · mechanism) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full | 25.0% (1/4) | — | 100.0% (8/8) | — | 24,507 | 1,868 | 98 | 2288 / 3830 ms | $47.22 | — | baseline |
| dedupe | 25.0% (1/4) | +0.0 [+0.0, +0.0] | 100.0% (8/8) | +0.0 [+0.0, +0.0] | 20,844 | 1,868 | 78 | 1923 / 2755 ms | $42.65 | 10% | pass · fail · pass |

Gates (registered in docs/prompt-tuning.md before round 1): quality, next action and intent each no more than 3 points below full; cost, at least 20% cheaper per turn; mechanism, fewer cached tokens read per turn and output no more than 10% longer.
Served model(s) read from the responses: gemini-3.8-flash. Stamp: n=8 call points per style (4 action points) · gemini-3.8-flash · 2026-09-26 · sample ab72e89ace15.

Gemini read the library from an explicit context cache (2 cache(s), 45,351 tokens, 0.04 hours alive), deleted at the end of the run. Its storage, at the unconfirmed price in core/models.py, came to $0.00 for this run and is not in the cost columns; creating it billed about $0.03 of input. In production one cache serves every conversation, at about $0.025 an hour.
