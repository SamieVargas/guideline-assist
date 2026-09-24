# Assist · 2026-09-24 · sample assist_100 (`ab72e89ace15`, 5 conversations)

## Part 3 · context ablation

Arm A: the full guideline library in a cached system prefix, one call a turn. Arm B: an intent call, then only that subflow's section in context. Latency is per turn (all calls that turn, retries included). Cost per 1,000 conversations = mean cost per turn x 13.10 assist triggers per conversation (agent utterances + agent actions per test conversation) x 1,000.

| Arm · model | Next action | Intent | Cache reads (tokens, share of input) | Mean input tokens / turn (uncached part) | p50 / p95 latency | Cost / 1,000 conversations | Stamp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A · `claude-haiku-4-5-20251001` | 25.0% (5/20) | 48.7% (19/39) | 1,157,646 (96.5%) | 30776.641 (386.6667) | 1660 / 3244 ms | $60.26 | n=39 · claude-haiku-4-5-20251001 · 2026-09-24 · sample ab72e89ace15 |

## Part 4 · assist evals (turn level)

| Arm · model | Intent (all points) | Intent turns 0–4 | Intent 5–9 | Intent 10–14 | Intent 15+ | Turns to stable intent (median / mean, never) | Next action (action points) | Slots exact (name right) | Slot value recall | `none_yet` false alarms (no-action points) | `none_yet` on action points | Citation valid | Validator pass · retries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A · `claude-haiku-4-5-20251001` | 48.7% (19/39) | 40.0% (2/5) | 33.3% (3/9) | 40.0% (2/5) | 60.0% (12/20) | 2 / 9.3333, never 2/5 | 25.0% (5/20) | 100.0% (2/2) | 100.0% | 36.8% (7/19) | 45.0% (9/20) | 100.0% (39/39) | 100.0% (39/39) · 4 |

Stamp per row: A·claude-haiku-4-5-20251001: n=39 · claude-haiku-4-5-20251001 · 2026-09-24 · sample ab72e89ace15 (20 action points, 19 no-action points)
