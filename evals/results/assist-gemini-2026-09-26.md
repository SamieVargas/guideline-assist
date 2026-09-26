# Assist · 2026-09-26 · sample assist_100 (`ab72e89ace15`, 100 conversations)

## Part 3 · context ablation

Arm A: the full guideline library in a cached system prefix, one call a turn. Arm B: an intent call, then only that subflow's section in context. Latency is per turn (all calls that turn, retries included). Cost per 1,000 conversations = mean cost per turn x 13.10 assist triggers per conversation (agent utterances + agent actions per test conversation) x 1,000.

| Arm · model | Next action | Intent | Cache reads (tokens, share of input) | Mean input tokens / turn (uncached part) | p50 / p95 latency | Cost / 1,000 conversations | Stamp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A · `gemini-3.8-flash` | 82.2% (287/349) | 87.7% (608/693) | 407,345 (2.2%) | 26467.3709 (25879.5714) | 10706 / 205342 ms | $262.50 | n=693 · gemini-3.8-flash · 2026-09-26 · sample ab72e89ace15 |

## Part 4 · assist evals (turn level)

| Arm · model | Intent (all points) | Intent turns 0–4 | Intent 5–9 | Intent 10–14 | Intent 15+ | Turns to stable intent (median / mean, never) | Next action (action points) | Slots exact (name right) | Slot value recall | `none_yet` false alarms (no-action points) | of which early (the agent's next action) | `none_yet` on action points | Citation valid | Validator pass · retries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · `gemini-3.8-flash` | 87.7% (608/693) | 80.4% (74/92) | 92.4% (182/197) | 87.0% (147/169) | 87.2% (205/235) | 4 / 5.5444, never 10/100 | 82.2% (287/349) | 88.8% (175/197) | 89.7% | 24.4% (84/344) | 38.1% (32/84) | 6.0% (21/349) | 100.0% (693/693) | 100.0% (693/693) · 12 |

A no-action point is an agent turn after which nothing is due before the customer speaks again. A false alarm there is "early" when the suggested action is the one the agent took next, after the customer replied: premature rather than wrong.

Stamp per row: A·gemini-3.8-flash: n=693 · gemini-3.8-flash · 2026-09-26 · sample ab72e89ace15 (349 action points, 344 no-action points)

Gemini ran through vertex; 90 overload or rate-limit answers were waited out and retried, and that waiting is not in the latency columns.
