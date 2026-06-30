# Citation Verifier Error Taxonomy

- repair id: `citation_verifier_repair_v0.1`
- baseline run: `specialist_cpu_first_training_20260630T030852Z`
- test rows: `31`
- test errors: `23`

## Failure Types

- `composite_claim`: 22
- `support_boundary_confusion`: 17
- `source_quality_feature_missing`: 10
- `hard_negative_overaccepted`: 8
- `partial_support_boundary`: 6
- `rare_negative_class_boundary`: 6
- `positive_support_missed`: 5

## Confusions

- `not_supported->partial_support`: 5
- `supports->not_supported`: 5
- `partial_support->not_supported`: 4
- `not_supported->supports`: 3
- `insufficient->partial_support`: 2
- `partial_support->contradicts`: 2
- `insufficient->not_supported`: 1
- `not_supported->contradicts`: 1
