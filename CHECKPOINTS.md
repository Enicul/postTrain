# Checkpoints

Use this file to resume work without guessing.

## CP-2026-06-30-001 - Repo initialization

Status: current

Local path:

```text
/Users/lucine/Documents/Job/projects/postTrain
```

Remote:

```text
git@github.com:Enicul/postTrain.git
```

Branch:

```text
main
```

What exists:

- root operating docs,
- learning-source registry,
- golden v0.1 data,
- specialist CPU baseline script,
- first baseline run artifacts.

GitHub state:

```text
main pushed
initial commit: 7d64753 docs: initialize post-training artifact repo
```

Resume:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain
git status --short
sed -n '1,220p' PROGRESS.md
sed -n '1,220p' TODO.md
```

## CP-2026-06-30-002 - Golden v0.1 data checkpoint

Path:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

Important contents:

```text
datasets/router_classifier
datasets/risk_reviewer
datasets/citation_verifier
long_research_trace_source_quality_repair_25
baselines/specialist_cpu_baselines_v0.1
```

Data boundary:

Social data is market radar and user-language seed. It is not truth unless
verified by official or auditable evidence.

## CP-2026-06-30-003 - Specialist CPU baseline v0.1

Status:

```text
complete
```

Command:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_baselines_v0.1
```

Output:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_baselines_v0.1
```

Verify:

```bash
cat training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_baselines_v0.1/logs/checkpoint.json
sed -n '1,120p' training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_baselines_v0.1/README.md
```

Next resume point:

```text
Start with citation_verifier/predictions_test.jsonl and create an error taxonomy.
```

## CP-2026-06-30-004 - Learning source registry

Status:

```text
created
```

Path:

```text
LEARNING_SOURCES.md
```

What exists:

- reusable entry template,
- first GLM ARC entry,
- explicit extracted / not-adopted / why-not structure,
- mapping from GLM ARC to KIWI/postTrain architecture.
- GLM verifier distinction: Reasoning RL outcome verifier vs Agentic RL
  process/tool-level verifier, mapped to KIWI process rewards.

Resume:

```text
Add Qwen, DeepSeek, Kimi, and MiniMax/WebExplorer entries using the same
structure before turning those notes into architecture or training changes.
```

## CP-2026-06-30-005 - First tracked CPU training batch

Status:

```text
complete
```

Command:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --run-id specialist_cpu_first_training_20260630T030852Z
```

Output:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_first_training_20260630T030852Z
```

Metrics:

| Specialist | Test accuracy | Test macro F1 | Interpretation |
| --- | ---: | ---: | --- |
| router_classifier | 0.9167 | 0.9368 | reproducible strong baseline |
| risk_reviewer | 0.5946 | 0.3986 | weak but above majority accuracy |
| citation_verifier | 0.2581 | 0.1441 | failed; repair data before GPU work |

Artifacts:

```text
config.json
manifest.json
logs/checkpoint.json
logs/events.jsonl
metrics.json
<dataset>/model.joblib
<dataset>/metrics.json
<dataset>/predictions_train.jsonl
<dataset>/predictions_dev.jsonl
<dataset>/predictions_test.jsonl
```

Resume:

```text
Start citation-verifier repair from the new run's
citation_verifier/predictions_test.jsonl. Group errors by source mismatch,
partial support, ambiguous label, insufficient evidence, and synthetic artifact.
```

## CP-2026-06-30-006 - Citation verifier repair v0.1

Status:

```text
complete
```

Commands:

```bash
python3 training-corpus/scripts/repair_citation_verifier.py \
  --repair-id citation_verifier_repair_v0.1

python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/repaired_datasets \
  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/baselines \
  --run-id citation_repair_probe_v0.1 \
  --datasets citation_verifier_url,citation_support_binary
```

Output:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1
```

Artifacts:

```text
README.md
error_taxonomy.md
error_taxonomy.json
test_error_audit.jsonl
probe_metrics.json
repaired_datasets/citation_verifier_url/
repaired_datasets/citation_support_binary/
baselines/citation_repair_probe_v0.1/
```

Metrics:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy |
| --- | ---: | ---: | ---: |
| original citation_verifier | 0.2581 | 0.1441 | 0.4839 |
| citation_verifier_url | 0.2581 | 0.1390 | 0.4839 |
| citation_support_binary | 0.3871 | 0.3767 | 0.5806 |

Decision:

The repair loop clarified the failure but did not make citation verification
ready for GPU fine-tuning. `trace_id` helps but is leakage; source URL/domain is
valid context but insufficient; binary support is clearer but still weak.

Resume:

```text
Create citation_verifier_repair_v0.2 with more hard negatives, clean positive
official spans, partial-support boundary cases, and rare insufficient/contradict
examples. Do not start citation-verifier GPU fine-tuning before this repair.
```

## CP-2026-06-30-007 - Citation verifier repair v0.2

Status:

```text
complete
```

Commands:

```bash
python3 training-corpus/scripts/build_citation_repair_v02.py

python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/repaired_datasets \
  --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2/baselines \
  --run-id citation_repair_probe_v0.2 \
  --datasets citation_verifier_url,citation_support_binary
```

Output:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.2
```

Artifacts:

```text
README.md
manifest.json
candidate_generation_pool.jsonl
repaired_datasets/citation_verifier_url/
repaired_datasets/citation_support_binary/
baselines/citation_repair_probe_v0.2/
```

Metrics:

| Dataset / probe | Train rows | Test accuracy | Test macro F1 | Majority accuracy |
| --- | ---: | ---: | ---: | ---: |
| citation_verifier_url | 178 | 0.3871 | 0.3333 | 0.4839 |
| citation_support_binary | 148 | 0.4194 | 0.4139 | 0.5806 |

Decision:

The v0.2 repair improved both probe families, especially five-way macro F1, but
still did not beat the majority baseline on test accuracy. Continue data repair
before GPU fine-tuning.

Resume:

```text
Create citation_verifier_repair_v0.3 from audited real citation spans: official
positive paragraphs, partial-support boundaries, and rare contradict /
insufficient rows. Keep dev/test fixed or create a separately named audited
golden set if the evaluation split changes.
```
