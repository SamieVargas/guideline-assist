# Post-call QA · 2026-09-23 · sample qa_100 (`e1aa3534dc5e`) · perturbation seed 20260927

Untouched: 100. Perturbed copies: remove 100, swap 99, value 59. A flag is `missed`, `out_of_order` or `wrong_value`.

## False flags on untouched conversations (read this first)

| QA · model | Conversations with any flag | Steps flagged | Stamp |
| --- | --- | --- | --- |
| rules (no model) | 63.0% (63/100) | 19.2% (66/344) | n=100 · rules (no model) · 2026-09-23 · sample e1aa3534dc5e |

## Recall per defect type (the expected status on the defective step)

| QA · model | remove → missed | swap → out_of_order | value → wrong_value | remove: any flag on the step | swap: any flag on the step | value: any flag on the step |
| --- | --- | --- | --- | --- | --- | --- |
| rules (no model) | 100.0% (100/100) | 100.0% (99/99) | 57.6% (34/59) | 100.0% (100/100) | 100.0% (99/99) | 57.6% (34/59) |

## Precision per flag

| QA · model | missed | out_of_order | wrong_value |
| --- | --- | --- | --- |
| rules (no model) | 100.0% (100/100) | 100.0% (99/99) | 16.7% (34/204) |

Precision counts every flag of that status across untouched and perturbed conversations; it is a true positive only on the planted step of a copy whose planted defect is that status.
