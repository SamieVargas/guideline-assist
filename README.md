# guideline-assist

Real-time agent assist and post-call QA on ASAPP's [Action-Based Conversations Dataset](https://github.com/asappresearch/abcd) (ABCD, NAACL 2021): turn-by-turn intent and next-action suggestions grounded in the company's written guidelines, with citations validated in code; a cached-full-policy versus retrieved-section latency ablation; post-call QA scored on labeled defects; shadow agreement against what the human agents actually did; an injection eval; and a deployment readout.

ABCD is about 10,000 customer-service chats role-played by trained crowdworkers for a fictional online retailer; they are real conversations between people and contain no real customers. MIT licence, Copyright (c) 2021 ASAPP Research ([data/README.md](data/README.md)). Nothing here claims anything about any vendor's product.

Plain Anthropic Python SDK, no framework. The assist proposes; nothing in this repo takes an action on anyone's behalf.

## Status

Parts 3 and 4 have run in full ([results](evals/results/assist-2026-09-24.md), 4,130 calls, $19.70). The other model runs are still to come. Every number is in `evals/results/`.

| Part | What | Script | State |
| --- | --- | --- | --- |
| 1 | Loader, guideline library with stable section ids, enums generated from the ontology, ingest report | `evals/ingest.py` | done, [ingest table](evals/results/ingest-2026-09-23.md) |
| 2 | Live-assist contract, native structured output with parser fallback, validator with one reject-and-retry | `core/assist.py`, `core/validate.py`, `core/llm.py` | done, tested with a stub client |
| 3 | Context ablation: arm A (full library, cached) vs arm B (intent call, then one section) | `evals/run_assist.py` | done 2026-09-24: arm A is cheaper and faster on both models |
| 4 | Turn-level assist evals on 100 frozen test conversations (349 action points, 344 no-action points) | `evals/run_assist.py` | done 2026-09-24; [guideline-order baseline](evals/results/assist-baseline-2026-09-23.md) alongside |
| 5 | Conversation-level intent on 300 frozen test conversations | `evals/run_intent.py` | ready; ~$1.04 both models; [majority baseline](evals/results/intent-baseline-2026-09-23.md) |
| 6 | Post-call QA on 100 untouched + 258 perturbed copies (remove 100, swap 99, value 59) | `evals/run_qa.py` | ready; ~$2.03 on Sonnet; [rule baseline](evals/results/qa-baseline-2026-09-23.md) |
| 7 | QA agreement with Samie's hand labels on 20 blind items | `evals/labeling/`, `evals/qa_agreement.py` | kit built, waiting on labels |
| 8 | Shadow agreement on 50 conversations | `evals/run_shadow.py` | ready; free after a Part 4 run of the same arm and model |
| 9 | Injection: 10 frozen fixtures × 5 runs | `evals/run_injection.py` | fixtures frozen; ~$0.63 |
| 10 | Deployment readout | `docs/deployment-readout.md`, `evals/readout_table.py` | skeleton and number table built; prose is Samie's |
| 11 | Replay viewer | `evals/export_viewer.py` | data export only; the page goes in samievargas.com after the tables exist |
| 12–14 | Streaming, concurrency sweep, fine-tuning | | not built (optional) |

## What the Parts 3–4 run says (100 test conversations, 2026-09-24)

| Arm · model | Next action | Intent | p50 / p95 per turn | Cost / 1,000 conversations |
| --- | --- | --- | --- | --- |
| A · Haiku 4.5 | 50.1% | 79.9% | 1.6 / 2.7 s | $48 |
| B · Haiku 4.5 | 53.3% | 74.2% | 2.7 / 4.3 s | $55 |
| A · Sonnet 5 | 73.9% | 88.0% | 2.1 / 3.2 s | $122 |
| B · Sonnet 5 | 72.8% | 75.9% | 3.7 / 5.8 s | $148 |

- Caching the whole 27,563-token library (arm A) is cheaper and faster than retrieving one section (arm B) on both models, because a cache read costs a tenth of fresh input and arm B spends a second call on intent. Arm B's intent is also worse. Arm A wins the ablation.
- Sonnet 5 on arm A gets the next action right 73.9% of the time without being told the intent, level with the guideline-order baseline that is told it (73.4%). Haiku is 24 points behind for 40% of the cost.
- Half of the "false alarms" (suggesting an action when nothing is due until the customer replies) are the action the agent took next: 64% of Sonnet A's. They are early rather than wrong; the table reports both.

## What the no-model numbers already say

- 11.4% of gold test actions are not in their conversation's guideline section, so validated next-action accuracy tops out at 88.6% (see [decisions](docs/decisions.md)).
- Told the gold intent, the dumbest possible assist (suggest the first required step not yet done) gets the next action right at 73.4% of action points, and false-alarms at 83.7% of points where nothing is due. That is the floor for Part 4.
- A rules-only QA catches every removed and swapped step but flags 63% of untouched conversations, which is why the model QA's false-flag rate is reported first.

## Run it

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/fetch_data.py          # the 37 MB conversation file, sha256-checked
python -m pytest -q tests/            # offline, no key

python evals/ingest.py                # Part 1
python evals/run_assist.py --baseline # no-model floors; also run_intent / run_qa / run_shadow --baseline

export ANTHROPIC_API_KEY=...
python evals/run_assist.py --arms A --models haiku --limit 5   # smoke: check real tokens against the estimate
python evals/run_assist.py            # Parts 3–4 (prints the estimate and asks before any call)
python evals/run_intent.py            # Part 5
python evals/run_qa.py                # Part 6
python evals/run_shadow.py --arm A --model haiku   # Part 8, the winning arm
python evals/run_injection.py --arm A --model haiku  # Part 9
python evals/readout_table.py         # Part 10 numbers
```

Every keyed script prints its cost estimate before any call; `--estimate-only` stops there, and without `--yes` it asks. Samples (`data/samples/`) and injection fixtures (`evals/fixtures/injection.json`) are drawn once with a recorded seed and hash; the scripts refuse to redraw them.

## Layout

- `core/` — loader, guideline library, generated enums, contracts, validator, model-call wrapper, assist arms, QA, perturbations, metrics.
- `evals/` — one script per part, results in `evals/results/` (markdown table + raw JSON records, every row stamped with n, model, date and sample hash).
- `docs/` — [decisions](docs/decisions.md), [provenance of ported patterns](docs/PROVENANCE.md), [deployment readout](docs/deployment-readout.md).
- Model ids and prices are pinned in one place, `core/models.py`.
