# Citation Verifier Repair v0.2

v0.2 is a train-only data repair experiment. It keeps original dev/test unchanged
and augments only the training split, so evaluation remains comparable to v0.1.

## Why

v0.1 showed the main failures were composite claims, support-boundary confusion,
hard negatives, and rare negative classes. Source URL/domain alone did not fix
the five-way task.

## Candidate Generation Rules

- `atomic_positive_from_supports_claim_part`: 34
- `hard_negative_cross_trace_overlap`: 40
- `missing_evidence_insufficient`: 30
- `original`: 108
- `partial_support_boundary_upsample`: 20

## Selected Training Strategy

- `citation_verifier_url`: original train + `hard_negative_cross_trace_overlap` + `missing_evidence_insufficient`.
- `citation_support_binary`: original train + `hard_negative_cross_trace_overlap`.

This is based on a local ablation: using all generated rows improved some
dev metrics but hurt binary test performance. The selected strategy keeps
augmentation targeted instead of flooding the train split.

## Baseline Results

Command:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets \
  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/baselines \
  --run-id citation_repair_probe_v0.2 \
  --datasets citation_verifier_url,citation_support_binary
```

| Dataset | Train rows | Test accuracy | Test macro F1 | Majority accuracy |
| --- | ---: | ---: | ---: | ---: |
| citation_verifier_url | 178 | 0.3871 | 0.3333 | 0.4839 |
| citation_support_binary | 148 | 0.4194 | 0.4139 | 0.5806 |

Interpretation:

v0.2 improves the repair probes versus v0.1, but both tasks still underperform
the majority baseline on accuracy. This is evidence that the taxonomy is useful,
not evidence that the verifier is ready for GPU fine-tuning.

## Selected Generation Counts

### citation_verifier_url
- `hard_negative_cross_trace_overlap`: 40
- `missing_evidence_insufficient`: 30
- `original`: 108

### citation_support_binary
- `hard_negative_cross_trace_overlap`: 40
- `original`: 108


## Leakage Controls

- Only `train.jsonl` is augmented.
- Original `dev.jsonl` and `test.jsonl` are copied without generated rows.
- `trace_id` is retained in provenance for audit but is not a model feature.
- Missing `source_url` is normalized to an empty string, not the literal token `None`.

## Next

Create `citation_verifier_repair_v0.3` from audited real citation spans:
official positive paragraphs, partial-support boundaries, and rare contradict /
insufficient examples.
