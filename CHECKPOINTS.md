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

## CP-2026-07-01-001 - Real citation spans v0.1

Status:

```text
seed collected
```

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/real_citation_spans_v0.1
```

Command:

```bash
python3 training-corpus/scripts/collect_real_citation_spans_v01.py \
  --timeout-seconds 30
```

What exists:

- 29 real paragraph/list/table-cell citation rows;
- 5 source pages;
- 0 final fetch/anchor failures;
- baseline-compatible `citation_verifier` train/dev/test/all files;
- source hashes and paragraph hashes, but no raw HTML dumps.

Label distribution:

```text
verified_support: 15
partial_support: 6
insufficient: 4
contradicts: 4
```

Resume:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain
python3 - <<'PY'
import json, pathlib, collections
base = pathlib.Path("training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/real_citation_spans_v0.1")
rows = [json.loads(line) for line in (base / "spans/all.jsonl").read_text().splitlines() if line.strip()]
print(len(rows), collections.Counter(row["label"]["support_type"] for row in rows))
PY
```

Next:

Expand this seed to at least 100 audited rows before training
`citation_verifier_repair_v0.3`.

## CP-2026-07-01-002 - Report and filing source expansion plan

Status:

```text
planned
```

Path:

```text
docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md
```

What was decided:

- Continue from `real_citation_spans_v0.1`.
- Add richer sources: SEC filings, company financial reports, earnings releases,
  financial tables, transcripts, public research, and reputable news.
- Do not store full raw reports in Git.
- Do not ingest paywalled sell-side research report text.
- Treat social sources as radar/task seeds, not final truth.

Next target artifact:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/report_and_filing_spans_v0.1
```

Resume:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain
sed -n '1,220p' docs/REPORT_AND_FILING_SOURCE_PLAN_20260701.md
sed -n '1,180p' training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/real_citation_spans_v0.1/REPORT.md
```

## CP-2026-07-01-003 - Portfolio report checkpoint

Status:

```text
complete
```

Path:

```text
docs/PORTFOLIO_REPORT_20260701.md
```

What exists:

- compact interview claim;
- system-shape Mermaid diagram;
- current data asset table;
- router/risk/citation metric summaries;
- failure taxonomy;
- post-training relevance explanation;
- explicit "what we do not claim" section;
- next-work sequence.

Resume:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain
sed -n '1,260p' docs/PORTFOLIO_REPORT_20260701.md
```
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

## CP-2026-06-30-008 - AI expanded v0.1 data checkpoint

Status:

```text
imported
```

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Source:

```text
/Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1
```

Import command:

```bash
rsync -a --delete \
  /Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ \
  training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/
```

Selected rows:

| Dataset | Train | Dev | Test |
| --- | ---: | ---: | ---: |
| calculation_verifier | 2,000 | 500 | 500 |
| citation_verifier | 6,000 | 1,200 | 1,200 |
| event_extractor | 6,000 | 1,200 | 1,200 |
| grpo_rollouts | 8,000 | 1,600 | 1,600 |
| memo_quality_scorer | 8,000 | 1,600 | 1,600 |
| preference_pairs | 8,000 | 1,600 | 1,600 |
| risk_reviewer | 8,000 | 1,600 | 1,600 |
| router_classifier | 6,000 | 1,200 | 1,200 |
| sft_trajectories | 8,000 | 1,600 | 1,600 |

Decision:

This checkpoint is the larger server-portable training pack. Keep
`golden_v0.1` as the smaller, stricter social/bookmark-derived pack and use
this expanded pack for pipeline/GPU-readiness checks.

Resume:

```text
Use the canonical baseline in CP-2026-06-30-009. Do not judge model quality from
the expanded train/dev/test split alone; add realistic holdout evaluation first.
```

## CP-2026-06-30-009 - AI expanded CPU baseline v0.1

Status:

```text
complete
```

Canonical command:

```bash
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1 \
  --out-root training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines \
  --run-id specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Output:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z
```

Metrics:

| Specialist | Target | Test accuracy | Test macro F1 | Majority accuracy |
| --- | --- | ---: | ---: | ---: |
| router_classifier | route_label | 1.0000 | 1.0000 | 0.1667 |
| risk_reviewer | risk_level | 1.0000 | 1.0000 | 0.6669 |
| citation_verifier | support/verdict | 0.9000 | 0.8978 | 0.3333 |

Failure preserved:

An earlier run used the placeholder id
`specialist_cpu_ai_expanded_v0.1_20260630T000000Z`. It is retained as a
non-canonical artifact and documented in `FAILURE_LOG.md`; use the timestamped
run above for reporting.

Decision:

The expanded data is learnable, but router/risk scores are too clean to claim
real-world generalization. Treat this as a CPU sanity baseline and GPU-readiness
checkpoint, not as proof that the specialists are production-ready.

Resume:

```text
Build a realistic holdout evaluator for real tool traces, long-research
episodes, and harder evidence-chain negatives. Run this checkpoint against that
holdout before starting LoRA/SFT/DPO/GRPO.
```

## CP-2026-06-30-010 - Realistic holdout eval v0.1

Status:

```text
complete
```

Command:

```bash
python3 training-corpus/scripts/evaluate_baseline_holdouts.py \
  --run-id realistic_holdout_eval_v0.1_20260630T083000Z
```

Output:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/baselines/specialist_cpu_ai_expanded_v0.1_20260630T080225Z/holdouts/realistic_holdout_eval_v0.1_20260630T083000Z
```

Evaluated holdouts:

| Holdout | Dataset | Rows | Accuracy all rows | Accuracy seen-labels only | Schema gap |
| --- | --- | ---: | ---: | ---: | --- |
| golden_v0.1_router_all | router_classifier | 344 | 0.3023 | 0.3611 | yes |
| golden_v0.1_risk_all | risk_reviewer | 181 | 0.2762 | 0.4464 | yes |
| golden_v0.1_citation_all | citation_verifier | 166 | 0.4819 | 0.6957 | yes |
| long_research_repair_25_router_all | router_classifier | 25 | 0.4800 | 0.4800 | no |
| long_research_repair_25_risk_all | risk_reviewer | 25 | 0.0000 | n/a | yes |
| long_research_repair_25_citation_all | citation_verifier | 417 | 0.0000 | n/a | yes |
| real_tool_trace_pilot_10_router | router_classifier | 10 | 0.0000 | 0.0000 | yes |

Failure preserved:

The first run failed because the event logger received `path` both as the log
file argument and as an event payload key. The script was patched to emit
`source_path` instead, then rerun successfully with the same run id.

Decision:

This holdout confirms that the expanded train/dev/test split is too easy for
router/risk quality claims. The next work is data-contract repair:
`risk_review` and `clarification_needed` must be represented in router labels;
`medium` must be represented in risk labels; citation labels need an explicit
mapping between `candidate_evidence`, `partial_support`, `insufficient`,
`contradicts`, and the expanded verifier labels.

Resume:

```text
Start with metrics/confusion matrices and capped error samples. For older runs,
`real_tool_trace_pilot_10_router/errors.jsonl` and
`golden_v0.1_router_all/errors.jsonl` exist, but new runs should use
`error_samples*.jsonl` by default. Build a router boundary repair dataset that
includes real tool traces, risk_review, clarification_needed, and evidence_check
vs deep_research distinctions.
```

## CP-2026-06-30-011 - Recording protocol migration

Status:

```text
complete
```

Changed:

- Added `docs/RECORDING_PROTOCOL.md`.
- `train_specialist_baselines.py` now defaults to summary recording.
- `evaluate_baseline_holdouts.py` now defaults to summary recording.
- Full row-level output requires `--record-mode full`.
- `AGENTS.md`, `CODEX.md`, `docs/SERVER_RUNBOOK.md`, `DECISIONS.md`,
  `FAILURE_LOG.md`, `PROGRESS.md`, and `TODO.md` now point future work toward
  bounded local artifacts.

Verified:

```text
python3 -m py_compile training-corpus/scripts/train_specialist_baselines.py training-corpus/scripts/evaluate_baseline_holdouts.py
python3 training-corpus/scripts/train_specialist_baselines.py --help
python3 training-corpus/scripts/evaluate_baseline_holdouts.py --help
router-only summary smoke in /tmp/posttrain-recording-smoke
holdout summary smoke in /tmp/posttrain-holdout-recording-smoke
```

Resume:

```text
Continue data-contract repair. New runs should use summary mode by default and
inspect `error_samples*.jsonl`, not full `errors.jsonl`, unless a full-mode run
is explicitly requested.
```

## CP-2026-06-30-012 - Router contract repair v0.1c

Status:

```text
complete
```

Current router repair checkpoint:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c
```

Canonical baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/baselines/router_contract_repair_probe_v0.1c_20260630T143244Z
```

Canonical holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_contract_repair_v0.1c/baselines/router_contract_repair_probe_v0.1c_20260630T143244Z/holdouts/router_contract_repair_holdout_eval_v0.1c_20260630T143256Z
```

Key results:

| Holdout | Old acc | v0.1c acc | Schema gap after repair |
| --- | ---: | ---: | --- |
| golden_v0.1_router_all | 0.3023 | 0.8895 | no |
| long_research_repair_25_router_all | 0.4800 | 0.9600 | no |
| real_tool_trace_pilot_10_router | 0.0000 | 1.0000 | no |

Resume:

```text
Do not start GPU router fine-tuning yet. Next router step is
router_social_boundary_repair_v0.1 for long social/bookmark claims that are
still sometimes downgraded to fast_answer.
```

## CP-2026-06-30-013 - Router social boundary candidate v0.1

Status:

```text
candidate
```

Candidate repair:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1
```

Baseline:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/baselines/router_social_boundary_probe_v0.1_20260630T143757Z
```

Holdout eval:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/router_social_boundary_repair_v0.1/baselines/router_social_boundary_probe_v0.1_20260630T143757Z/holdouts/router_social_boundary_holdout_eval_v0.1_20260630T143807Z
```

Results:

| Holdout | Router v0.1c | Social v0.1 |
| --- | ---: | ---: |
| golden_v0.1_router_all | 0.8895 | 0.9012 |
| long_research_repair_25_router_all | 0.9600 | 0.9600 |
| real_tool_trace_pilot_10_router | 1.0000 | 0.9000 |

Decision:

Do not promote this to canonical yet. It improves social/bookmark routing but
regresses one real-tool deep-research row.

Resume:

```text
Next main task is risk_contract_repair_v0.1. Router social repair can resume
later by adding real-tool-style capex/source-support deep-research anchors.
```

## CP-2026-07-02-001 - Report and filing spans v0.1

Status:

```text
collected, sanity-checked, awaiting label audit
```

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/report_and_filing_spans_v0.1
```

Command:

```bash
python3 training-corpus/scripts/collect_report_and_filing_spans_v01.py \
  --timeout-seconds 45
```

What exists:

- 102 real spans from 22 sources: 51 SEC filing rows (10-K/10-Q/6-K for NVDA,
  AMD, MSFT, MU, META, GOOGL, AMZN, AVGO, TSM), 25 earnings-transcript rows
  (NVDA, AMD, MSFT, GOOGL, AMZN, AVGO), 18 public research rows (SIA x3,
  Deloitte 2026 outlook), 8 reputable news rows (AP x2);
- labels: verified_support 48, contradicts 26, partial_support 15,
  insufficient 13; splits: train 46 / dev 31 / test 25;
- every row keeps source_url, source_type, source_tier, section,
  evidence_span, source hash, paragraph hash, published_at, as_of, and
  license_note; no raw HTML/PDF dumps;
- `sanity_check.json` shows all plan targets pass;
- `failures.json` preserves scouting fallbacks (Gartner 403, IDC 404,
  fool.com pagination, DDG bot wall, missing MU transcript).

Verify:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain
python3 - <<'PY'
import json, pathlib, collections
base = pathlib.Path("training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/report_and_filing_spans_v0.1")
rows = [json.loads(line) for line in (base / "spans/all.jsonl").read_text().splitlines() if line.strip()]
print(len(rows), collections.Counter(r["label"]["support_type"] for r in rows))
print(json.loads((base / "sanity_check.json").read_text())["targets"])
PY
```

Resume:

```text
Run the label audit over all 131 real span rows (29 seed + 102 new), then a
citation CPU probe on the combined audited pack under summary recording.
Only then define citation_verifier_repair_v0.3. GPU work stays blocked.
```

## CP-2026-07-02-002 - Audited frozen citation eval v1

Status:

```text
frozen
```

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/citation_real_eval_v1
```

What exists:

- 131 audited rows (labels V62/P21/I16/C32; splits 62/38/31);
- per-row `audit` block with both blind votes and adjudication notes;
- 3 corrections (2.3%), original labels preserved, zero test-split changes;
- conventions C1/C2/C3 pinned in `AUDIT_REPORT.md` + `audit/adjudications.json`;
- source-pack SHA256 hashes in `manifest.json`.

Verify:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain
python3 - <<'PY'
import json, pathlib, collections
base = pathlib.Path("training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/citation_contract_repair_v0.1/citation_real_eval_v1")
rows = [json.loads(l) for l in (base/"rows/all.jsonl").read_text().splitlines()]
print(len(rows), collections.Counter(r["label"]["support_type"] for r in rows))
print(collections.Counter(r["audit"]["status"] for r in rows))
PY
```

Resume:

```text
Block A2: build risk_contract_repair_v0.1b from real long-research
medium-risk rows and freeze the repaired risk holdout. Then Block B
(rules/naive/engineered prompt arms on frozen holdouts).
```

## CP-2026-07-02-003 - Risk contract repair v0.1b + frozen risk eval

Status:

```text
complete; risk_real_eval_v1 frozen
```

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1b
```

Commands:

```bash
python3 training-corpus/scripts/build_risk_contract_repair_v01b.py --audit-dir <audit dir>
python3 training-corpus/scripts/train_specialist_baselines.py \
  --data-dir .../risk_contract_repair_v0.1b/repaired_datasets \
  --out-root .../risk_contract_repair_v0.1b/baselines \
  --run-id risk_contract_repair_probe_v0.1b_20260702T031246Z \
  --datasets risk_reviewer
```

What exists:

- `risk_real_eval_v1/rows/{dev,test,all}.jsonl`: 90 audited real rows with
  per-row blind votes and adjudication notes; conventions R1-R5 in
  `risk_real_eval_v1/audit/risk_adjudications.json`;
- `repaired_datasets/risk_reviewer/`: train 8,395 (8,229 v0.1 synthetic +
  166 normalized real, 51 rule-synced), dev/test = the audited real rows;
- probe run `risk_contract_repair_probe_v0.1b_20260702T031246Z`: dev/test
  accuracy 0.84/0.83, medium recall 1.00/1.00 (v0.1: 0.0), high/gate recall
  0.64/0.73, majority 0.42.

Verify:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain
python3 - <<'PY'
import json, pathlib, collections
base = pathlib.Path("training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/repairs/risk_contract_repair_v0.1b")
rows = [json.loads(l) for l in (base/"risk_real_eval_v1/rows/all.jsonl").read_text().splitlines()]
print(len(rows), collections.Counter(r["label"]["risk_level"] for r in rows))
print(collections.Counter(r["audit"]["status"] for r in rows))
PY
```

Resume:

```text
Block A is complete (citation_real_eval_v1 + risk_real_eval_v1 frozen).
Next: Block B - hand-rules arm and naive/engineered prompt arms on the
frozen rulers, temperature 0, cost logged per episode under the
rollout_store_v0.1 schema.
```

## CP-2026-07-02-004 - Act 1 killed at rung 4 (risk hybrid arm)

Status:

```text
complete; Act 1 closed without training
```

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/rung4_risk_hybrid_v0.1
training-corpus/scripts/risk_gate_rules_v11.py
```

What exists:

- risk_explib_v1 (5 opus-extracted dev-only lessons + L6 owner policy record);
- hybrid predictions (haiku, sonnet; anonymized ids), final scores;
- gate rules v1.1 as versioned code (contract- and dev-derived only);
- REPORT.md with the safety-regression story and the dissent trail.

Result:

hybrid sonnet 0.978 acc / 1.000 gate recall / 0 gate FP -> kill criteria MET
(haiku 0.900/1.000 also passes).

Ladder state:

Act 1 KILLED (rung 4), Act 2 KILLED (rung 3), Act 3 sole weights candidate.

Resume:

```text
Act 3 escalation environment: cost table from real KIWI traces, cheap-path
outcome table via Block C K=8 rollouts on train/dev seeds, argmax-label SFT
collapse baseline, lambda sweep (2-3 values). Then Block E under the hard
budget cap (24 A100h / ~USD 100 / 5 evenings).
```
