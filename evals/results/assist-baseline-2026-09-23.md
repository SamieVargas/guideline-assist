# Assist baseline (guideline order, gold intent given) · 2026-09-23 · sample assist_100 (`ab72e89ace15`, 100 conversations)

## Part 3 · context ablation

Arm A: the full guideline library in a cached system prefix, one call a turn. Arm B: an intent call, then only that subflow's section in context. Latency is per turn (all calls that turn, retries included). Cost per 1,000 conversations = mean cost per turn x 13.10 assist triggers per conversation (agent utterances + agent actions per test conversation) x 1,000.

| Arm · model | Next action | Intent | Cache reads (tokens, share of input) | Mean input tokens / turn (uncached part) | p50 / p95 latency | Cost / 1,000 conversations | Stamp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline · `none` | 73.4% (256/349) | 100.0% (693/693) | 0 (n/a) | 0.0 (0.0) | n/a (no model) | $0.00 | n=693 · none · 2026-09-23 · sample ab72e89ace15 |

## Part 4 · assist evals (turn level)

| Arm · model | Intent (all points) | Intent turns 0–4 | Intent 5–9 | Intent 10–14 | Intent 15+ | Turns to stable intent (median / mean, never) | Next action (action points) | Slots exact (name right) | Slot value recall | `none_yet` false alarms (no-action points) | `none_yet` on action points | Citation valid | Validator pass · retries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline · `none` | 100.0% (693/693) | 100.0% (92/92) | 100.0% (197/197) | 100.0% (169/169) | 100.0% (235/235) | 4 / 4.1, never 0/100 | 73.4% (256/349) | 0.0% (0/177) | 0.0% | 83.7% (288/344) | 0.9% (3/349) | 100.0% (693/693) | 100.0% (693/693) · 0 |

Stamp per row: baseline·none: n=693 · none · 2026-09-23 · sample ab72e89ace15 (349 action points, 344 no-action points)
