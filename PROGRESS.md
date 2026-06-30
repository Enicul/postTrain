# Progress

Last updated: 2026-06-30

## Current State

The repo has been initialized as a standalone post-training artifact repo for
KIWI interview preparation.

Imported from the Agent/KIWI workspace:

- golden training corpus `golden_v0.1`,
- CPU specialist baseline script,
- baseline requirements,
- first CPU baseline run artifacts.

Initial GitHub push is complete.

```text
remote: git@github.com:Enicul/postTrain.git
branch: main
initial commit: 7d64753 docs: initialize post-training artifact repo
learning source registry commit: d048963 docs: add learning source registry
```

## Current Checkpoint

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1
```

Important subpaths:

```text
datasets/
baselines/specialist_cpu_baselines_v0.1/
baselines/specialist_cpu_first_training_20260630T030852Z/
repairs/citation_verifier_repair_v0.1/
```

## Baseline Results

| Specialist | Target | Test accuracy | Test macro F1 | Status |
| --- | --- | ---: | ---: | --- |
| router_classifier | route_label | 0.9167 | 0.9368 | usable first baseline |
| risk_reviewer | risk_level | 0.5946 | 0.3986 | weak baseline |
| citation_verifier | support_type | 0.2581 | 0.1441 | data repair needed |

Latest tracked training run:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/baselines/specialist_cpu_first_training_20260630T030852Z
```

## Interpretation

- Router is the first credible specialist baseline.
- Risk reviewer is directionally useful but too weak to use as a gate alone.
- Citation verifier failed on held-out data. `citation_verifier_repair_v0.1`
  produced an error taxonomy and repair probes, but the result still points to
  data repair before GPU work.

## Citation Verifier Repair v0.1

Repair pack:

```text
training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1
```

Top error types:

| Failure type | Count |
| --- | ---: |
| composite_claim | 22 |
| support_boundary_confusion | 17 |
| source_quality_feature_missing | 10 |
| hard_negative_overaccepted | 8 |
| partial_support_boundary | 6 |
| rare_negative_class_boundary | 6 |
| positive_support_missed | 5 |

Repair probe results:

| Dataset / probe | Test accuracy | Test macro F1 | Majority accuracy | Status |
| --- | ---: | ---: | ---: | --- |
| original citation_verifier | 0.2581 | 0.1441 | 0.4839 | failed baseline |
| citation_verifier_url | 0.2581 | 0.1390 | 0.4839 | source URL/domain alone did not help |
| citation_support_binary | 0.3871 | 0.3767 | 0.5806 | clearer task, still weak |

Decision:

Do not start citation-verifier GPU fine-tuning yet. Build
`citation_verifier_repair_v0.2` with more hard negatives, cleaner positive
official spans, partial-support boundary cases, and rare negative examples.

## Learning Source Registry

`LEARNING_SOURCES.md` has been added as the canonical place to record external
model reports and what we extracted from them.

Current source entries:

| Source | Status | Extracted use |
| --- | --- | --- |
| GLM ARC: Agentic + Reasoning + Coding | adopted as architecture framing | use ARC to explain why KIWI needs reasoning, verifier-rich tasks, agentic loops, and process-level verifiers, while not claiming a GLM-scale unified model |

## Last Verified Commands

```bash
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
python3 training-corpus/scripts/train_specialist_baselines.py --run-id smoke_router_only2 --datasets router_classifier --out-root /tmp/posttrain-baseline-smoke2
python3 training-corpus/scripts/train_specialist_baselines.py --run-id specialist_cpu_first_training_20260630T030852Z
python3 training-corpus/scripts/repair_citation_verifier.py --repair-id citation_verifier_repair_v0.1
python3 training-corpus/scripts/train_specialist_baselines.py --data-dir training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/repaired_datasets --out-root training-corpus/runs/x-bookmarks-recent-111-20260629/curated/golden_v0.1/repairs/citation_verifier_repair_v0.1/baselines --run-id citation_repair_probe_v0.1 --datasets citation_verifier_url,citation_support_binary
git push -u origin main
```

The imported baseline checkpoint reports:

```json
{"status": "complete", "run_id": "specialist_cpu_baselines_v0.1"}
```

## Next Best Step

Continue citation verifier data repair and learning-source registry:

1. build `citation_verifier_repair_v0.2`,
2. add hard negatives and cleaner positive / partial / insufficient examples,
3. rerun the repair baseline,
4. only then decide whether a small LLM verifier is worth GPU time,
5. add Qwen, DeepSeek, Kimi, and MiniMax/WebExplorer source entries using the
   same extracted / not-adopted structure.
