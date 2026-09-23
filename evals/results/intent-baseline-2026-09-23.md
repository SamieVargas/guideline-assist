# Baseline · conversation-level intent · 2026-09-23 · sample intent_300 (`ce4b21d5c1a7`)

Full transcript without ACTION lines, one of 55 subflows. Macro-F1 averages over the subflows present in the sample.

| Model | Accuracy | Macro-F1 | Top confused pairs (count) | Validator pass | Mean latency | Cost (run) | Stamp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `majority class from train (recover_username)` | 2.3% (7/300) | 0.0009 | recover_password ↔ recover_username (13); recover_username ↔ shirt (12); out_of_stock_general ↔ recover_username (10); recover_username ↔ search_results (10); manage ↔ recover_username (10) | 100.0% (300/300) | 0.0 ms | $0.00 | n=300 · majority class from train (recover_username) · 2026-09-23 · sample ce4b21d5c1a7 |
