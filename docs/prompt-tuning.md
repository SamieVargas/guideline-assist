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
| r1 | library styles full, dedupe, nosub, outline, bare | tune_60 | not run yet | |
