# Data: ABCD (Action-Based Conversations Dataset)

ASAPP Research, NAACL 2021 ("Action-Based Conversations Dataset: A Corpus for Building More In-Depth Task-Oriented Dialogue Systems", Chen et al.). Source: [github.com/asappresearch/abcd](https://github.com/asappresearch/abcd), pinned here to commit `6b8700ce67c6b37b062dd7a60abc76d7ef832a97` (2022-01-26).

About 10,000 human-to-human customer-service chats for a fictional online clothing retailer ("AcmeBrands"). The chats were role-played by trained crowdworkers, with the agents incentivized to follow the written guidelines; they are real conversations between people and contain no real customers. Any page built from this data should say exactly that.

## Licence

MIT, read from the source repo's `LICENSE` file on 2026-09-23 ("Copyright (c) 2021 ASAPP Research"); a copy is committed as [`abcd/LICENSE`](abcd/LICENSE). This matches the third-party listing the brief mentioned.

## Files

`python scripts/fetch_data.py` downloads what is missing from the pinned commit and checks every file's sha256. The small files are committed; the conversation file is not (37 MB).

| File | Committed | sha256 (first 16) | What is actually in it (checked 2026-09-23) |
| --- | --- | --- | --- |
| `abcd_v1.1.json.gz` | no | `2bdf53ac359543dc` | `{"train": 8034, "dev": 1004, "test": 1004}` conversations. Each has `convo_id`, `scenario` (personal, order, product, `flow`, `subflow`), `original` (a list of `[speaker, text]`, speaker ∈ customer, agent, action) and `delexed` (the same turns, lowercased and delexicalized, each with `targets`). |
| `ontology.json` | yes | `2e1c1d763518ba08` | `intents` (10 flows, 55 subflows), `actions` (30 actions in three categories with their slot names), `values` (enumerable slot values), `next_steps`, `vocabulary`. |
| `kb.json` | yes | `7b1cdb1002e33534` | subflow id → the ordered list of required actions. |
| `guidelines.json` | yes | `9264557941df24fe` | flow display name → `description` and `subflows`, each with `actions` (button, type, text, subtext) and `instructions`. Names are display text, not ontology ids. |
| `abcd_sample.json` | yes | `151e0c487493ab37` | three conversations in the same shape, used by the offline tests. |
| `utterances.json` | no, not used | | the agent-utterance candidate pool for the paper's retrieval task. |

## What the loader relies on

- `original` and `delexed` are parallel, turn by turn (checked on every load; 0 mismatches over 10,042 conversations).
- On an action turn, `delexed[i].targets` is `[subflow, "take_action", action_name, slot_values, -1]`. The action name and slot values come from there; the original action text ("Account has been pulled up for Chloe Zhang.") is what the model sees next to them.
- The intent label is `targets[0]` (identical on every turn of a conversation, always an ontology subflow id), not `scenario.subflow`, which carries a variant suffix (`timing_4`, `shirt_how_2`) and in 33 conversations a name outside the ontology (`status_questions` 30, `status_delivery_date` 3).
- The delexicalized turns are kept in the loaded file for any comparison with the paper's setup; nothing in the evals uses them as model input.

## Splits

Nothing is built or tuned on `test`. Every reported number is on a sample of `test` drawn once by `evals/freeze_samples.py` with a recorded seed and frozen with the sha256 of its ids in `samples/`.
