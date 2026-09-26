# Prompt tuning · round confirm · 2026-09-26 · claude-sonnet-5 arm A · sample assist_100 (`ab72e89ace15`, test split, 100 conversations)

Each row is the same call points with the guideline library rendered at a different length. Deltas are paired against `full` point by point, in percentage points with a 95% interval. Cost per 1,000 conversations = mean cost per turn x 13.10 x 1,000.

| Library | Next action | Δ next action vs full | Intent | Δ intent vs full | Cache reads / turn | Uncached input / turn | Output / turn | p50 / p95 latency | Cost / 1,000 conversations | Cut vs full | Gates (quality · cost · mechanism) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full | 73.4% (256/349) | — | 87.5% (606/693) | — | 37,926 | 359 | 87 | 2006 / 2385 ms | $121.98 | — | baseline |
| dedupe | 76.2% (266/349) | +2.9 [+0.0, +5.7] | 87.3% (605/693) | -0.1 [-1.6, +1.3] | 31,389 | 360 | 87 | 2084 / 2580 ms | $104.55 | 14% | pass · fail · pass |

Gates (registered in docs/prompt-tuning.md before round 1): quality, next action and intent each no more than 3 points below full; cost, at least 20% cheaper per turn; mechanism, fewer cached tokens read per turn and output no more than 10% longer.
Served model(s) read from the responses: claude-sonnet-5. Stamp: n=693 call points per style (349 action points) · claude-sonnet-5 · 2026-09-26 · sample ab72e89ace15.
