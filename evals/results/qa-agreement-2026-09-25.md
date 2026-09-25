# QA agreement with hand labels · 2026-09-25 · 20 items (10 untouched, 10 perturbed, blind) · model `claude-sonnet-5`

| Pair | Exact status agreement (per step) | Cohen's kappa | Flag / no-flag agreement | Stamp |
| --- | --- | --- | --- | --- |
| model vs samie | 85.3% (58/68) | 0.5844 | 85.3% (58/68) | n=68 · claude-sonnet-5 · 2026-09-25 · sample labeling-kit |
| samie vs construction | 94.1% (64/68) | 0.8218 | 94.1% (64/68) | n=68 · claude-sonnet-5 · 2026-09-25 · sample labeling-kit |
| model vs construction | 91.2% (62/68) | 0.7512 | 91.2% (62/68) | n=68 · claude-sonnet-5 · 2026-09-25 · sample labeling-kit |

| Item kind | Steps | Model vs Samie |
| --- | --- | --- |
| remove | 17 | 88.2% (15/17) |
| swap | 9 | 77.8% (7/9) |
| untouched | 33 | 87.9% (29/33) |
| value | 9 | 77.8% (7/9) |

Disagreements (model vs Samie):

- L01 offer-refund: model wrong_value, Samie followed, construction followed
- L02 verify-identity: model wrong_value, Samie followed, construction wrong_value
- L03 search-policy: model out_of_order, Samie followed, construction followed
- L07 shipping-status: model wrong_value, Samie followed, construction wrong_value
- L09 enter-details: model followed, Samie out_of_order, construction out_of_order
- L12 search-timing: model followed, Samie out_of_order, construction followed
- L12 select-faq: model followed, Samie out_of_order, construction followed
- L16 enter-details: model out_of_order, Samie followed, construction followed
- L17 search-membership: model followed, Samie out_of_order, construction out_of_order
- L18 verify-identity: model wrong_value, Samie followed, construction followed
