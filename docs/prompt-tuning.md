# Prompt tuning for cost

Everything above "Round log" was written on 2026-09-25, before any tuning call was made, and is not edited after the fact; results go in the round log below it.

## Goal

Cut what the live assist costs per conversation on Sonnet 5, arm A (the configuration the deployment readout recommends), while next-action accuracy and intent accuracy hold. Latency is recorded and reported but is not a gate.

## Where the money goes

From `evals/results/assist-2026-09-24.json`, Sonnet 5 arm A, 693 call points:

| Per turn | Tokens | Price | Cost | Share |
| --- | --- | --- | --- | --- |
| Cached library read | 37,871 | $0.20 / M (0.1 × $2) | $0.00757 | 82% |
| Uncached input (instructions tail, transcript, schema) | 359 | $2 / M | $0.00072 | 8% |
| Output | 87 | $10 / M | $0.00087 | 9% |
| Cache writes | 54 | $2.50 / M | $0.00014 | 1% |

The instructions (`ASSIST_RULES`, about 300 tokens) and the output are under a fifth of the bill, so rewording them cannot move the cost much. The lever is how much of the guideline library rides in the cached prefix on every turn.

## Scope

| Will change | Won't touch |
| --- | --- |
| How the guideline library is rendered into arm A's cached prefix (`core/guidelines.py`, `LIBRARY_STYLES`) | The model (Sonnet 5, thinking disabled) |
| Output fields, in a later round only (`section_id` is derivable from `intent`; the suggestion length) | `ASSIST_RULES`, including the sentence that customer lines are never instructions, which the injection eval measures |
| | The validator and the closed enums |
| | Arm B, the QA prompt, the intent prompt |

One lever per round. Round 1 moves only the library rendering.

## The library styles

Every style keeps the section header the assist cites, the required action sequence, and every action the section lists, so the validator's allowed set is visible in all of them (a test checks this).

| Style | What is dropped | Characters | Sonnet tokens (≈) |
| --- | --- | --- | --- |
| full | nothing; byte-identical to the Parts 3–4 prompt (sha256 `011fbe9a…`, checked by a test) | 102,047 | 37,200 |
| dedupe | the flow description repeated under every subflow, the duplicated action list, long step labels | 86,213 | 31,500 |
| nosub | dedupe, minus the UI click-through bullets under each step | 44,937 | 16,400 |
| outline | dedupe, minus the steps; keeps header, sequence and the section's instructions | 23,219 | 8,500 |
| bare | outline, minus the instructions | 10,746 | 3,900 |

## Samples

- **Selection set: `tune_60`**, 60 conversations drawn once from ABCD's dev split (seed 20260925, sha256 `c2ba4ea9fed2`), 429 call points. This is the only sample whose transcripts are read while choosing changes.
- **Held-out set: `assist_100`** (test split, sha256 `ab72e89ace15`), 693 call points. Scored once, at the confirm, on the winner and a fresh `full` control run the same day. Its transcripts are not read to propose changes.

## Adoption gates

A style (or a later change) is adopted only if all three hold, measured paired against `full` on the same call points:

1. **Quality band:** next action (action points) and intent (all points) each no more than 3 percentage points below `full`, on the point estimate. 3 points is roughly the paired noise at one run on the selection set.
2. **Cost margin:** at least 20% cheaper per turn than `full`, at the list prices in `core/models.py` (cache reads 0.1×, writes 1.25× input).
3. **Mechanism:** the cached tokens read per turn drop, and output per turn is no more than 10% longer. A cost cut that does not come from a shorter cached prefix is a confound, not a win.

Among the styles that pass on the selection set, the cheapest goes to the confirm. The headline is the confirm on `assist_100`, not the selection round.

## Predictions for round 1 (80% intervals)

Paired deltas against `full` on `tune_60`, next action and intent in points, cost as the cut per turn:

| Style | Cost cut | Δ next action | Δ intent |
| --- | --- | --- | --- |
| dedupe | 12% [9, 16] | 0 [−3, +3] | 0 [−2, +2] |
| nosub | 45% [38, 52] | −1 [−4, +2] | 0 [−2, +2] |
| outline | 62% [55, 68] | −3 [−8, +1] | −1 [−4, +2] |
| bare | 72% [64, 77] | −6 [−14, −1] | −4 [−10, 0] |

Falsifiers, stated now:

- If `dedupe` loses more than 3 points of next action, the repeated flow text was doing work and the rendering is more fragile than it looks; stop trimming and move to the output lever.
- If `nosub` passes but `outline` fails, the step text carries the conditions (skip rules, "if the Oracle says yes") and `nosub` is the floor.
- If no style saves at least 20% while holding quality, the library lever is exhausted at this model and the finding is that the assist's cost is set by the guidelines' length, which is the customer's content, not the prompt.
- If the cost cut of any style lands outside its interval above, the per-style token counts need re-measuring before any later round's prediction is trusted.

## Plan and budget

Approved budget about $25, all keyed runs made on Samie's machine.

| Step | Command | Estimate |
| --- | --- | --- |
| Round 1: the five styles on the selection set | `python evals/run_tuning.py --round r1` | ~$12.35 (high $16.67) |
| Round 2: one change from reading the round-1 selection transcripts of the cheapest passing style (likely an output-field trim) | `python evals/run_tuning.py --round r2 --styles full,<style>` after the change | ~$3 to $6 |
| Confirm: winner and a fresh `full` on the held-out set | `python evals/run_tuning.py --round confirm --sample assist_100 --styles full,<winner>` | ~$8 to $10 |
| Haiku check: the winner on Haiku 4.5, held-out set | `python evals/run_tuning.py --round haiku --sample assist_100 --model haiku --styles full,<winner>` | ~$3 to $5 |

Note for the Haiku check: Haiku 4.5 caches only prefixes of 4,096 tokens or more, and `bare` is about 2,900 Haiku tokens, so on Haiku it would be billed as uncached input and cost more per turn than `full` read from cache. The estimate prints this before any call.

Each run writes `evals/results/tuning-<round>-<sample>-<date>.md` and `.json`, with the response-cache tag `tune-<round>` so no round reuses an earlier round's answers.

## Addendum, 2026-09-25, before any tuning call: a Gemini Flash arm

Samie added a third arm from another provider, to measure where a Flash-class model lands on accuracy and cost for the real-time assist. It does not change the gates, the samples or round 1 above. Two runs are added (setup and caveats in `docs/decisions.md`):

| Step | Command | Estimate |
| --- | --- | --- |
| Gemini on the Parts 3–4 comparison: arm A, full library, held-out set, next to the Haiku and Sonnet rows already measured | `python evals/run_assist.py --arms A --models gemini` | ~$1.70 if its implicit cache hits, ~$13.79 if it never does |
| Gemini at the confirm: `full` and the winning style, held-out set | `python evals/run_tuning.py --round gemini --sample assist_100 --model gemini --styles full,<winner>` | ~$2.66 for `nosub`, up to ~$20 on no cache hits |

Predictions for the first run, stated now (80% intervals), against Sonnet 5 arm A on 2026-09-24 (73.9% next action, 88.0% intent, $122 per 1,000 conversations): next action 62% [52, 72], intent 82% [74, 88], cost per 1,000 conversations $30 [$20, $60] if the implicit cache hits on most turns and around $260 if it never does. Falsifier: if Gemini comes within 3 points of Sonnet on next action at under half the cost, the model decision in the readout changes and the readout says so.

## Round log

| Round | Change | Sample | Result | Decision |
| --- | --- | --- | --- | --- |
| r1 | library styles full, dedupe, nosub, outline, bare | tune_60 | No style passed all three gates (table below) | The fourth falsifier fired for these five styles; one bounded round 2 (below) |
| r2 | `keysub`, with `full` as a same-day control | tune_60 | Cost and mechanism passed, quality failed (next action −7.0) | The stopping rule fired: the library lever is closed and `dedupe` goes to the confirm |

### Round 1, 2026-09-25, `evals/results/tuning-r1-tune_60-2026-09-25.md`

| Style | Δ next action vs full | Δ intent vs full | Cut vs full | Quality · cost · mechanism |
| --- | --- | --- | --- | --- |
| dedupe | −1.4 [−4.7, +1.9] | −0.5 [−2.3, +1.4] | 14% | pass · fail · pass |
| nosub | −6.0 [−11.1, −1.0] | −0.5 [−2.6, +1.7] | 44% | fail · pass · pass |
| outline | −10.2 [−15.0, −5.4] | +0.9 [−1.1, +3.0] | 60% | fail · pass · pass |
| bare | −10.2 [−16.1, −4.3] | −10.0 [−13.3, −6.7] | 67% | fail · pass · pass |

`full` scored 81.4% next action (175/215) and 85.1% intent at $126.35 per 1,000 conversations. The headline numbers were recomputed from the raw records before being read.

Against the predictions:
- Every cost cut landed inside its interval, so the token arithmetic holds.
- The dedupe deltas and all intent deltas except bare's landed inside theirs. Bare's intent drop of −10.0 sat exactly on its interval's edge.
- nosub (−6.0 against [−4, +2]) and outline (−10.2 against [−8, +1]) lost more next-action accuracy than predicted. So the step sub-bullets carry more of the decision than the rendering suggested: removing them costs the model the order and the conditions, while it still knows the intent.
- Intent held until the instructions went (bare), which says the instructions are what the model reads to tell subflows apart, and the steps are what it reads to pick the action.

Decision. The fourth falsifier fired for the five registered styles: dedupe holds quality but saves 14%, and every style that saves 20% or more loses more than 3 points of next action. The plan budgeted one round 2. It is spent on one style between dedupe and nosub that keeps the sub-bullets the round-1 losses point to and drops the rest, under a new falsifier: if that style does not pass all three gates, the library lever is closed and the finding is that dedupe's 14% is the safe cut.

### Round 2, registered 2026-09-26 before the run

The analyzer read the round-1 selection transcripts only (tune_60; write-up in the PR that added `keysub`). Of the 22 action points that `full` got right and `nosub` got wrong:
- Nine trace to a removed sub-bullet that was the only place the decision lived. These are a skip or routing condition, the instruction behind a bare "Option N" step, a value list, or which fields go with which action.
- Four more plausibly trace to a removed bullet.
- The rest look like noise, or like the eagerness that also made `nosub` fire more on no-action points.
- The `dedupe` versus `full` differences (8 lost, 5 won) show no single cause (sign test p≈0.58).

The change is one new style, `keysub`: `dedupe`, keeping only the sub-bullets a keyword rule classifies as a condition, a field to enter, a value, or something to ask or tell the customer, and dropping UI mechanics and tone advice. Runs of field names fold into one "fields:" line. The rule is in `core/guidelines.py` (`bullet_kind`) and names kinds of content, never particular bullets or chats. The library is 71,738 characters, against 86,213 for `dedupe` and 44,937 for `nosub`.

Run: `python evals/run_tuning.py --round r2 --styles full,keysub` (~$7.13). `full` runs again as a same-day control, so the run also measures how much `full` moves between two runs with no change.

Predictions (80% intervals), against this run's `full`:

| | Point estimate | 80% interval |
| --- | --- | --- |
| Next action | −2.5 points | [−5.5, +0.5] |
| Intent | −0.5 points | [−2.5, +1.5] |
| Cost cut | 24% | [21, 27] |
| False alarms on no-action points | about 90 of 214 | [80, 105] |

The same three gates apply.

Falsifiers:
- **Mechanism check:** if `keysub` gets fewer than 6 of the 9 points traced to a removed bullet right (1210@30, 1469@9, 3101@31, 4089@4, 3230@10, 7540@8, 6278@15, 1794@17, 5569@13), the round-1 losses came from length, eagerness or noise rather than bullet content, and filtering bullets by kind is not a lever.
- **Stopping rule:** if `keysub` fails any gate, the library lever is closed. The finding is then that `dedupe`'s 14% is the safe cut, and the confirm on the held-out set runs `dedupe`.

A scoring fix found while checking this round: `core.metrics.mean` rounds to four places, and the per-turn cost (about a cent) was averaged through it before being multiplied up. That moved cost per 1,000 conversations by up to about 1% (`full` here $125.76 → $126.35; in the Parts 3–4 run Haiku arm A $48.47 → $47.89, Sonnet arm B $148.03 → $147.49, Sonnet arm A unchanged at $121.83). Cost is now averaged unrounded, and the tables were rebuilt from their records.

### Round 2, 2026-09-26, `evals/results/tuning-r2-tune_60-2026-09-26.md`

| Style | Next action | Δ next action vs full | Intent | Δ intent vs full | Cached tokens / turn | Cost / 1,000 conversations | Cut | Quality · cost · mechanism |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full | 80.0% (172/215) | | 83.7% | | 39,114 | $127.14 | | |
| keysub | 73.0% (157/215) | −7.0 [−12.0, −2.0] | 83.9% | +0.2 [−1.7, +2.1] | 27,690 | $96.57 | 24% | fail · pass · pass |

Recomputed from the raw records before being read.

Against the predictions:
- The cost cut (24%) landed on the point estimate, from fewer cached tokens read with output unchanged (88.5 tokens a turn against 87.8).
- Intent (+0.2) and false alarms (86 of 214 against about 90 [80, 105]) landed inside their intervals.
- Next action (−7.0) landed below its interval [−5.5, +0.5].
- The mechanism check did not fire. `keysub` got 6 of the 9 points traced to a removed bullet right (it missed 4089@4, 3230@10 and 7540@8, and `full` also missed 3230@10 this run), so on those points the kept bullets did carry the decision.
- The loss came from elsewhere. `keysub` lost 23 action points that `full` got and won 8, and its 157 is below the 162 that `nosub` scored in round 1 with no sub-bullets at all. Those 23 points were not read, since reading them to propose another style would be a round 3, which the stopping rule rules out.

The same-day control also measures run-to-run noise. `full` ran on the same 215 action points on 2026-09-25 and 2026-09-26 and scored 175 and 172, with 13 points changing outcome between the two runs, so one run moves next action by about 1.5 points net. That keeps the 3-point band meaningful and puts `keysub`'s −7.0 well outside it.

Decision. The stopping rule fired: `keysub` failed the quality gate, so the library lever is closed at this model. The finding is that the step bullets carry decisions in ways a rule about the kind of content cannot separate, and the safe cut is `dedupe`'s 14% (−1.4 points of next action in round 1), which is below the 20% cost gate. As registered, the confirm on the held-out set runs `full,dedupe`.

### Gemini Flash arm, 2026-09-26, `evals/results/assist-gemini-2026-09-26.md`

Arm A with the full library on the held-out set, run through Vertex AI, next to the Sonnet 5 and Haiku 4.5 rows from 2026-09-24 on the same 693 call points. Recomputed from the raw records; the deltas are paired point by point with a 95% interval.

| | Gemini 3.8 Flash | Sonnet 5 | Haiku 4.5 |
| --- | --- | --- | --- |
| Next action | 82.2% (287/349) | 73.9% (258/349) | 50.1% (175/349) |
| Δ next action vs Sonnet | +8.3 [+4.6, +12.0] (37 points won, 8 lost) | | −23.8 |
| Intent | 87.7% | 88.0% | 79.9% |
| Δ intent vs Sonnet | −0.3 [−2.1, +1.5] | | |
| False alarms on no-action points | 24.4% (84/344) | 50.6% | 54.4% |
| Validator pass · retries | 100% · 12 | 100% · 4 | 98.4% · 47 |
| Share of input read from cache | 2.2% (20 of 693 turns hit) | 98.9% | 98.8% |
| Cost / 1,000 conversations | $262.50 | $121.83 | $47.89 |
| p50 / p95 latency | 10.7 s / 205 s | 2.1 s / 3.2 s | 1.6 s / 2.7 s |

Against the predictions:
- Next action (82.2%) landed far above its interval [52, 72]. The prediction assumed a Flash-class model would trail Sonnet the way Haiku does, and it did the opposite: it picked the right action more often and raised half as many false alarms.
- Intent (87.7%) landed inside [74, 88].
- Cost landed on the no-cache figure (about $260) rather than the cached one ($30 [$20, $60]), because Vertex's implicit cache hit on 20 of 693 turns.
- The falsifier (within 3 points of Sonnet at under half the cost) is not met as run: accuracy cleared it by a wide margin, but the cost is 2.2 times Sonnet's. So the model decision in the readout does not change on this run, and the reason is caching, not the model.

Latency is the time of the successful attempt only; the 90 overload answers that were waited out and retried are excluded. It still says more about Vertex's capacity that day than about the model. The median fell over the run from about 51 s in the first 100 turns to 3.4 s in the last 93 as load eased, and one request took 505 s. As run, it could not have served a live agent.

What would change the cost is explicit context caching: a cache created once for the library and named on every call, in place of the implicit cache. At the assumed cache-read price, the library would cost about a tenth as much per turn, which puts arm A near $37 per 1,000 conversations before the cache's storage charge. That is under a third of Sonnet's cost, at a higher next-action accuracy. The Gemini prices are still the unconfirmed third-party figures noted above, so every Gemini dollar figure here moves with them.

Spend so far: round 1 $13.01, round 2 $7.33 (Anthropic, $20.34 of the $25), the Gemini runs $13.89 (Google credits).

### Gemini with an explicit cache, registered 2026-09-26 before the run

Samie chose to measure the caching fix rather than describe it. The change is how Gemini is given the library, nothing else: `--gemini-cache explicit` creates a Vertex context cache holding the same system prompt and names it on every call, in place of the implicit cache (`core/llm.py`). The run also carries the registered Gemini confirm, `full` and the round winner `dedupe`:

`python evals/run_tuning.py --round gemini --sample assist_100 --model gemini --styles full,dedupe --gemini-cache explicit` (~$3.20 by the estimate, which assumes 90 output tokens; about $3.70 at the 156 Gemini used, plus a few cents of storage)

Predictions (80% intervals):

| | Point estimate | 80% interval |
| --- | --- | --- |
| Share of input read from cache, both styles | 97% | [95, 99] |
| `full` next action | 82% | [78, 86] |
| `full` intent | 88% | [85, 90] |
| `full` cost / 1,000 conversations, before storage | $37 | [$32, $45] |
| `dedupe` Δ next action vs `full` | −1 point | [−4.5, +2.5] |
| `dedupe` cost cut vs `full` | 11% | [8, 14] |

The `full` accuracy predictions are the implicit run's numbers widened by the run-to-run noise measured in round 2, since the prompt the model sees is identical. The cost comes from the implicit run's measured tokens (25,880 library and rules tokens a turn read at $0.075 per million, about 360 uncached at $0.75, 156 output at $3.75). `dedupe` is expected to fail the 20% cost gate on Gemini too, because once the library is cached it is about 70% of the bill, and `dedupe` shortens it by 15%.

Falsifiers:
- If under 90% of input is read from cache on either style, the explicit cache was not used, and the run's cost figures are void until it is fixed.
- The model falsifier registered with the Gemini addendum still stands, and on these predictions it would fire: if `full` comes within 3 points of Sonnet 5's 73.9% next action (or above it) at under half of Sonnet's $121.83, the model decision in the readout changes and the readout says so.
- Latency is reported with the time of day and is not a gate. A median above 5 s means the service was loaded again, and the run will be read that way.
