# Citation Verifier Repair v0.1

This repair pack is generated from the first tracked citation verifier baseline.
It does not overwrite `golden_v0.1`; it creates audit artifacts and dataset variants.

## Baseline Problem

- Five-way citation support classification underperformed on held-out data.
- Test accuracy was `0.2581`; test macro F1 was `0.1441`.
- The majority baseline test accuracy was `0.4839`.

## Error Taxonomy

- `composite_claim`: 22
- `support_boundary_confusion`: 17
- `source_quality_feature_missing`: 10
- `hard_negative_overaccepted`: 8
- `partial_support_boundary`: 6
- `rare_negative_class_boundary`: 6
- `positive_support_missed`: 5

## Probe Metrics

| Probe | Dev acc | Dev macro F1 | Test acc | Test macro F1 |
| --- | ---: | ---: | ---: | ---: |
| 5way_base | 0.1852 | 0.1484 | 0.2581 | 0.1441 |
| 5way_source_url | 0.2222 | 0.2533 | 0.2581 | 0.139 |
| 5way_url_plus_trace_leakage_probe | 0.3333 | 0.3726 | 0.4839 | 0.3622 |
| binary_base | 0.2593 | 0.2582 | 0.3871 | 0.3845 |
| binary_source_url | 0.2963 | 0.2963 | 0.3871 | 0.3767 |
| binary_url_plus_trace_leakage_probe | 0.4444 | 0.432 | 0.5484 | 0.5363 |

## Decision

- `trace_id` is useful diagnostically but should not become a model feature because it leaks task identity.
- `source_url`/domain is allowed as source context, but the normalized v0.1 probe does not solve the task.
- A scratch probe that rendered missing URLs as literal `None` overstated the source-URL gain; this pack normalizes missing URLs to empty strings.
- Binary any-support detection is easier to explain as stage 1, but still does not solve the data problem alone.
- Next repair should add hard negatives and more clean positive/partial/insufficient spans.

## Artifacts

- `error_taxonomy.json`
- `error_taxonomy.md`
- `test_error_audit.jsonl`
- `probe_metrics.json`
- `repaired_datasets/citation_verifier_url/`
- `repaired_datasets/citation_support_binary/`
