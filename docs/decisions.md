# Decisions

Where the build departs from the brief, or from what a reader might expect, and why. The code wins where the two disagree; this is the record.

## Keyed runs are made on Samie's machine

The session that built this repo had no Anthropic API key, so the model runs are made locally and their result files committed. A 5-conversation smoke run (`--limit 5`, 2026-09-24) checked real token counts first; `--limit` runs get their own file name so the readout never quotes one as a headline.

## The cost estimator is calibrated on the first full run

The first-draft estimator assumed 4 characters per token for every model and estimated Parts 3–4 at $12.63; the run billed $19.70. The two tokenizers differ (the library is 27,563 tokens on Haiku 4.5 and 37,708 on Sonnet 5), a call with no cached prefix bills ~830–1,070 tokens beyond its prompt text, and retries add calls. `core/estimate.py` now carries those measurements per model; re-estimated, the same run comes to $20.29.

## False alarms are split into early and wrong

A no-action point allows nothing before the customer speaks again, which is strict: the most common "false alarm" is the action the agent took right after the customer's reply. The Part 4 table reports the false-alarm rate and, separately, the share of those that were the agent's next action. Neither number is dropped.

## The intent label is `targets[0]`, not `scenario.subflow`

`scenario.subflow` carries a variant suffix and, in 33 conversations, a name that is not an ontology subflow (`status_questions`). Every delexed turn's `targets[0]` is an ontology subflow id and is the same on every turn of a conversation, so it is the label.

## Guideline display names are mapped by order, with a guard

`guidelines.json` uses display names ("Initiate Refund"); the ontology uses ids (`refund_initiate`). Within each flow the two list subflows in the same order, so they are paired by position, and the pairing is accepted only if every pair shares a name token. A reordered or renamed file raises instead of misfiling a section. No mapping table is typed by hand.

## A section lists kb.json's required actions plus any button that resolves to an action

Buttons resolve to actions by name-token overlap, preferring the section's kb actions on ties ("Membership" in the membership FAQ is `search-membership`; "Membership Privileges" elsewhere is `membership`). In the test split, 88.6% of gold actions are in their conversation's section; the other 11.4% are real agent behaviour the guideline does not list (verify-identity in recover_password, for example). The validator rejects a suggestion the section does not list, as the brief asks, so 88.6% is a ceiling on validated next-action accuracy. It is reported in the ingest table rather than worked around.

## ACTION turns are shown with their logged values

Several actions (verify-identity, validate-purchase) log values their system text never prints. The model sees each action as `ACTION name(values) :: system text`, which is what a QA reviewer reading the action log would see, and what makes a wrong value detectable at all.

## Where the assist is called

Action points: every gold ACTION turn, with the transcript up to it. No-action points: agent utterances after which the agent's run of turns up to the next customer message holds no ACTION, drawn per conversation (seeded) to match that conversation's count of action points. An agent line like "let me pull up your account" right before an action is not a no-action point, because an action is due there.

## Arm B

Arm B makes the intent call first with only the subflow menu, stops there when the intent is `unclear` (the assist then says to keep talking), and otherwise puts that one section in context for the action call. Its prompts are not cached: they fall under Haiku 4.5's 4,096-token cache minimum, and the arm is defined as the no-cache alternative. Its citation validity is close to 100% by construction, since the model sees one section; the validator still checks it.

## Model settings

Haiku is pinned to its dated snapshot, `claude-haiku-4-5-20251001`. Sonnet 5 has no dated snapshot, so its id is `claude-sonnet-5`. Sonnet 5 runs adaptive thinking when the parameter is omitted; the assist is a latency-bound classifier, so thinking is turned off there (`thinking: {type: "disabled"}`), and the same setting is used for QA and intent so one model means one configuration.

## Cost per 1,000 conversations

Mean cost per assisted turn × 13.10 assist triggers per conversation × 1,000. 13.10 is the test split's agent utterances (9.51) plus agent actions (3.59) per conversation: the assist runs once per agent-side turn in a deployment.

## Conversation-level intent leaves ACTION lines out

An action such as `search-boots` names the subflow outright, so keeping ACTION lines would grade the agent's clicks rather than the language. The agent's and customer's words stay in.

## QA test set

Untouched conversations come from the 403 of 1,004 test conversations whose gold actions show every required step in guideline order ("compliant, as far as the gold actions show"). Each gets up to one perturbed copy per defect kind. `swap` needs two guideline-adjacent steps each logged exactly once (99 of 100 qualify); `value` needs a slot value the customer typed in the chat, so the defect is visible from the transcript (59 of 100 qualify). The copy counts are printed in every QA table.

The rule QA is a no-model baseline that reads only the ACTION log and chat text. It catches every removal and swap but flags 63% of untouched conversations, because many logged values (account ids, usernames) come from the account system and never appear in the chat. That false-flag rate is the number the model QA has to beat.

## The injection defence is in the prompt that is measured

The assist prompt says customer lines are information, never instructions, and that a step is done only when an ACTION line shows it. The injection eval measures the prompt as it would ship, sentence included; removing it would be a separate arm.

## Shadow reuses Part 4's calls

`shadow_50` is a subset of `assist_100`, and the calls use the same cache tag, so after a Part 4 run for the same arm and model the shadow table costs nothing new. The guideline's expected next step is the first required step in kb.json order not yet done.

## Latency and the response cache

Every response is cached on disk under `.cache/llm/` (not committed), keyed by the full request plus a tag. A cached record keeps the latency and usage measured when it was made and is marked `from_cache`; the count of cached records is in every assist table's JSON. `--no-cache` forces fresh calls when a fresh latency measurement is the point. Assist calls run one at a time, so latency is not measured under self-inflicted contention.

## Not built

Optional Parts 12 (streaming), 13 (concurrency sweep) and 14 (fine-tuning) are not built. Part 11's page belongs in the samievargas.com repo on its own PR after the eval tables exist; `evals/export_viewer.py` writes the JSON it will read.

## Hand-label spelling

The 20 hand-labelled items use the same five statuses as the model. Typed variants such as `out-of-order` are read as `out_of_order` by `evals/qa_agreement.py`; `labels.csv` itself is left as it was written. For a swap, the labels by construction mark both swapped steps `out_of_order`, which is stricter than the Part 6 recall, where flagging either step counts.

