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
https://github.com/Enicul/postTrain
```

Branch:

```text
main
```

What exists:

- root operating docs,
- golden v0.1 data,
- specialist CPU baseline script,
- first baseline run artifacts.

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
