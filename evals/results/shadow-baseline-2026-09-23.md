# Shadow agreement · 2026-09-23 · arm baseline · `guideline-order baseline` · sample shadow_50 (`7f064592ff08`)

| Measure | Result | Stamp |
| --- | --- | --- |
| Action agreement with the human's next action | 77.8% (137/176) | n=176 · guideline-order baseline · 2026-09-23 · sample 7f064592ff08 |
| Slot-value agreement (action agreed, human entered values) | 0.0% (0/101) | n=101 · guideline-order baseline · 2026-09-23 · sample 7f064592ff08 |
| Human's action was the guideline's next step | 77.8% (137/176) | n=176 · guideline-order baseline · 2026-09-23 · sample 7f064592ff08 |
| Disagreements: human deviated from the guideline, assist followed it | 36 | |
| Disagreements: assist wrong, human followed the guideline | 0 | |
| Disagreements: neither matched the guideline step | 3 | |

## Human deviated (assist right, human not)

| Conversation @ turn | Subflow | Human did | Assist suggested | Guideline next step |
| --- | --- | --- | --- | --- |
| 399 @ 3 | search_results | search-faq | try-again | try-again |
| 399 @ 5 | search_results | log-out-in | try-again | try-again |
| 399 @ 7 | search_results | instructions | try-again | try-again |
| 777 @ 4 | credit_card | pull-up-account | try-again | try-again |
| 777 @ 14 | credit_card | validate-purchase | try-again | try-again |
| 777 @ 15 | credit_card | ask-the-oracle | try-again | try-again |
| 1913 @ 14 | manage_dispute_bill | verify-identity | membership | membership |
| 1913 @ 18 | manage_dispute_bill | ask-the-oracle | membership | membership |
| 1913 @ 20 | manage_dispute_bill | ask-the-oracle | membership | membership |
| 1913 @ 27 | manage_dispute_bill | offer-refund | membership | membership |
| 2650 @ 17 | manage_cancel | offer-refund | membership | membership |
| 3294 @ 20 | return_size | enter-details | membership | membership |
| 3294 @ 23 | return_size | update-order | membership | membership |
| 4539 @ 8 | out_of_stock_general | record-reason | notify-team | notify-team |
| 4539 @ 15 | out_of_stock_general | make-purchase | promo-code | promo-code |
| 4618 @ 8 | manage_dispute_bill | verify-identity | pull-up-account | pull-up-account |
| 4618 @ 13 | manage_dispute_bill | offer-refund | pull-up-account | pull-up-account |
| 4618 @ 14 | manage_dispute_bill | offer-refund | pull-up-account | pull-up-account |
| 4889 @ 8 | search_results | log-out-in | try-again | try-again |
| 4889 @ 11 | search_results | instructions | try-again | try-again |
| 4961 @ 22 | refund_initiate | enter-details | record-reason | record-reason |
| 4961 @ 24 | refund_initiate | offer-refund | record-reason | record-reason |
| 5397 @ 14 | recover_password | verify-identity | enter-details | enter-details |
| 5492 @ 15 | mistimed_billing_already_returned | update-order | membership | membership |
| 6071 @ 2 | bad_price_yesterday | record-reason | pull-up-account | pull-up-account |
| 6156 @ 10 | status_due_date | enter-details | send-link | send-link |
| 6156 @ 11 | status_due_date | update-account | send-link | send-link |
| 6686 @ 15 | status_due_amount | enter-details | send-link | send-link |
| 6957 @ 16 | refund_update | membership | offer-refund | offer-refund |
| 6957 @ 21 | refund_update | enter-details | offer-refund | offer-refund |
| 6957 @ 22 | refund_update | update-order | offer-refund | offer-refund |
| 7049 @ 13 | mistimed_billing_never_bought | update-order | membership | membership |
| 7066 @ 10 | manage_extension | update-account | membership | membership |
| 7066 @ 11 | manage_extension | update-account | membership | membership |
| 8137 @ 13 | promo_code_invalid | promo-code | membership | membership |
| 8141 @ 19 | return_size | enter-details | update-order | update-order |

## Assist wrong

| Conversation @ turn | Subflow | Human did | Assist suggested | Guideline next step |
| --- | --- | --- | --- | --- |
| none | | | | |

## Neither on the guideline step

| Conversation @ turn | Subflow | Human did | Assist suggested | Guideline next step |
| --- | --- | --- | --- | --- |
| 812 @ 20 | status_delivery_time | update-order | none_yet | (all required steps done) |
| 2808 @ 20 | status_due_amount | update-account | none_yet | (all required steps done) |
| 7989 @ 28 | status_due_amount | update-account | none_yet | (all required steps done) |
