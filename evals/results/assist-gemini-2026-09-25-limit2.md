# Assist · 2026-09-25 · sample assist_100 (`ab72e89ace15`, 2 conversations)

## Part 3 · context ablation

Arm A: the full guideline library in a cached system prefix, one call a turn. Arm B: an intent call, then only that subflow's section in context. Latency is per turn (all calls that turn, retries included). Cost per 1,000 conversations = mean cost per turn x 13.10 assist triggers per conversation (agent utterances + agent actions per test conversation) x 1,000.

| Arm · model | Next action | Intent | Cache reads (tokens, share of input) | Mean input tokens / turn (uncached part) | p50 / p95 latency | Cost / 1,000 conversations | Stamp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A · `gemini-3.8-flash` | 28.6% (2/7) | 100.0% (13/13) | 0 (0.0%) | 26211.9231 (26211.9231) | 36083 / 238961 ms | $262.68 | n=13 · gemini-3.8-flash · 2026-09-25 · sample ab72e89ace15 |

## Part 4 · assist evals (turn level)

| Arm · model | Intent (all points) | Intent turns 0–4 | Intent 5–9 | Intent 10–14 | Intent 15+ | Turns to stable intent (median / mean, never) | Next action (action points) | Slots exact (name right) | Slot value recall | `none_yet` false alarms (no-action points) | of which early (the agent's next action) | `none_yet` on action points | Citation valid | Validator pass · retries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · `gemini-3.8-flash` | 100.0% (13/13) | 100.0% (1/1) | 100.0% (3/3) | 100.0% (1/1) | 100.0% (8/8) | 3 / 13.5, never 0/2 | 28.6% (2/7) | n/a | n/a | 66.7% (4/6) | 0.0% (0/4) | 0.0% (0/7) | 100.0% (13/13) | 100.0% (13/13) · 0 |

A no-action point is an agent turn after which nothing is due before the customer speaks again. A false alarm there is "early" when the suggested action is the one the agent took next, after the customer replied: premature rather than wrong.

Stamp per row: A·gemini-3.8-flash: n=13 · gemini-3.8-flash · 2026-09-25 · sample ab72e89ace15 (7 action points, 6 no-action points)

Gemini ran through vertex; 6 overload or rate-limit answers were waited out and retried, and that waiting is not in the latency columns.
