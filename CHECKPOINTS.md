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

## CP-2026-07-02-005 - Act 3 env arms; ladder provisionally closed without training

Status:

```text
complete (provisional kill; full engineered sweep deferred, spend-limited)
```

Path:

```text
training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/act3_env_arms_v0.1
```

What exists:

- rules / naive_sonnet policies scored on full 256; engineered_sonnet on 64
  (batch 1, spend-limited);
- env_arm_scores.json (all lambdas), REPORT.md with the ceiling-match finding
  and honesty limits.

Result:

Full 256: ORACLE 0.955/0.865/0.730 (gate 1.0); rules 0.760 (gate .625);
naive 0.666 (gate .672). Batch-1 (64): engineered_sonnet = ORACLE exactly at
all three lambdas, gate 1.0.

Ladder state:

Act 1 KILLED (rung 4, code gate floor), Act 2 KILLED (rung 3), Act 3
PROVISIONALLY killed (rung 3, 64/256). Zero GPU training used.

Resume:

```text
Next spend cycle: complete engineered sweep (haiku + sonnet, batches 2-4)
over the remaining 192 seeds. If the ceiling match holds, close the ladder
and write the final portfolio narrative. If it breaks, build argmax-SFT +
GRPO on escalation_env_v0.1 under the budget cap (24 A100h / ~USD 100) with
the concrete target the break reveals.
```

## CP-2026-07-02-006 - RL Phase 2 scaffolding ready (A/B/C)

Status:

```text
non-GPU scaffolding complete and CPU-smoke-verified; GPU + inference steps pending
```

Paths:

```text
docs/RL_PHASE2_SMALL_MODEL_PLAN.md
training-corpus/scripts/rl/            (Plan A trainers/eval, B env, C loop)
training-corpus/scripts/expand_env_seeds.py
.../ladder/escalation_env_v0.1/env_seeds_v0.2.json   (1,120 seeds)
```

Verify:

```bash
cd /Users/lucine/Documents/Job/projects/postTrain/training-corpus/scripts/rl
ENV=../../runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/ladder/escalation_env_v0.1
python3 reward_escalation.py $ENV
python3 citation_agentic_env.py
python3 training_free_grpo.py
```

Resume:

```text
On the A100: follow training-corpus/scripts/rl/README.md - A1 motivation
gate (prompted small model), then A2 argmax-SFT, then A3 GRPO with the
pre-registered kill check. Also complete the Act-3 192-seed engineered sweep
next spend cycle. Plan B: grow the citation corpus to 300-500 rows, then
GRPO on citation_agentic_env. Plan C: run training_free_grpo with an
inference backend as the no-weights control column.
```

## CP-2026-07-02-007 - Decision-node recording spec + retrospective module round

Status:

```text
QA audit complete (218/218); retrospective core module shipped in KIWI working
tree (uncommitted by rule); recording spec written and committed here.
```

Paths (postTrain, this repo):

```text
docs/DECISION_NODE_RECORDING_SPEC.md   (authoritative recording contract)
docs/DECISION_REVIEW_AND_TRAINING_FLYWHEEL.md   (the why)
```

KIWI side (Agent repo - NOT touched from here):

```text
src/retrospective/   (snapshot/maturation/quadrant/aggregate/exporter)
                     8 files, 25/25 tests, append-only SQLite, uncommitted
```

Audit findings:

```text
21 decision nodes mapped; 4 P0 recording gaps; 3 guardrail contradictions.
See DECISION_NODE_RECORDING_SPEC.md for the full inventory + fix plan.
```

Resume:

```text
Blocked step: land or stash the ~118 uncommitted KIWI files, THEN implement
the 4 P0 recording fixes and wire the retrospective module via the adapter
layer. Independent of that block: fix the 3 guardrail contradictions
(disclaimer default-on, buy-now output scrubber, dual-gate routing) and design
the capability-stage model (flywheel goal (a), currently 0 implementation).
See TODO.md "P1 - Retrospective Recording", D-2026-07-02-009, F-2026-07-02-009.
```

## CP-2026-07-03-001 - RL GPU-launch hardening (checkpoints, provenance, failure preservation)

Status:

```text
A1->A2->A3 escalation RL scripts hardened for owner pull-and-run on one A100.
CPU-smoke verified; not yet run on GPU. Ready to pull and launch A1.
```

Paths (postTrain, this repo):

```text
training-corpus/scripts/rl/run_logging.py     (NEW: run-dir provenance, manifest, log callback)
training-corpus/scripts/rl/monitor_run.py     (NEW: zero-dep watchdog)
training-corpus/scripts/rl/GPU_RUNBOOK.md     (NEW: owner step-by-step + failure protocol)
training-corpus/scripts/rl/sft_escalation.py  (run-dir, seed, grad-accum, resume, parent-run, save_total_limit)
training-corpus/scripts/rl/grpo_escalation.py (same + generations.jsonl + reward_trace.jsonl + save-steps)
training-corpus/scripts/rl/eval_escalation_policy.py (minor: --seed / set_seed)
training-corpus/scripts/rl/requirements-rl.txt (pinned == known-good, trl 0.11.4 era)
training-corpus/scripts/rl/README.md          (run-dir usage, 7B arm note, env_seeds_v0.2 note)
.gitignore                                    (run weights/checkpoints off git)
```

What each run now produces (in out-dir/<run_id>/):

```text
run_manifest.json   run_id, git_sha, seed, argv, config, env_seeds_version,
                    base_model, parent_run_id, pip_freeze
trainer_log.jsonl   every on_log dict + timestamp
generations.jsonl   (GRPO) per-completion: step, seed_id, completion, plan, reward
reward_trace.jsonl  (GRPO) per-batch: mean_reward, gate_violation_rate, action_mix
metrics.json, adapter/, checkpoint-*/
```

Resume:

```text
Pull the repo to the A100. Follow scripts/rl/GPU_RUNBOOK.md: CPU smoke, then
A1 prompted-eval (motivation gate), then A2 SFT, A3 GRPO - each into its own
out-dir/<run_id>/. Run monitor_run.py in a second terminal. On any failure:
keep the dir, write a FAILURE_LOG.md entry, re-run with --parent-run <run_id>.
See D-2026-07-03-001, TODO.md "P0 - RL Phase 2".
```

## CP-2026-07-03-002 - RL Phase 2 GPU session A1->A2->A3 run and written up

Status:

```text
A1->A2->A3 chain RAN on one A100 80GB (env v0.3, test n=48, lambda=0.3, seed 0).
SFT is the win; GRPO verdict recorded honestly (does not meet promotion bar).
All evidence rsynced to scripts/rl/runs/ and committed (weights git-excluded).
```

Headline results (test @lambda=0.3, oracle 0.8473):

```text
A1 prompted:  0.5B 0.3063 / 1.5B 0.6444 / 3B 0.4232 / 7B 0.7447
              -> no kill-pass; small models lack GATE discipline (not success)
A2 SFT:       0.5B 0.6061 (gate 0.50) / 1.5B 0.7495 (gate 0.875)
              -> trained 1.5B BEATS prompted 7B (0.7495 > 0.7447), 4.7x smaller
A3 GRPO:      0.5B 0.383 gate 0.00 COLLAPSE / 1.5B 0.7981 (+4.9) gate 0.875
              -> pre-registered verdict: GRPO not promoted at these scales
```

Evidence paths (postTrain, this repo; weights excluded by .gitignore):

```text
runs/a1_prompted/{qwen05,qwen15,qwen3,qwen7}_test_eval.json, a1_manifest.json
runs/sft_qwen05/20260703T1505Z-e571324/   (final 0.5B SFT)
runs/sft_qwen15/20260703T1506Z-e571324/   (final 1.5B SFT)
runs/grpo_qwen05/20260703T1507Z-e571324/  (0.5B collapse - generations/reward_trace)
runs/grpo_qwen15/20260703T1520Z-e571324/  (1.5B healthy)
runs/sft_qwen{05,15}/20260703T1504Z-e571324/  (preserved failed launches)
runs/gpu_session_20260703/{run_a1,run_a2,run_a3}.sh, sft_train.jsonl, *batch.log
```

Note: the 6 run_manifest.json files had their tensorboard `logging_dir` hostname
suffix REDACTED before commit (redaction_note field kept); no other infra
identifiers were present. Per-run pip_freeze records the authoritative env
(trl==0.15.2).

Resume:

```text
SFT 1.5B is the promotable policy; GRPO is not promoted. Next-iteration GRPO
options are pre-registered (not committed) in D-2026-07-03-003: gate-seed
oversampling, larger K, gate exploration bonus, or accept the hybrid. Near-term
TODO wins: DPO round on existing preference_pairs, failure-trajectory taxonomy
from grpo_qwen05 generations.jsonl, identify the 1-missed-gate seed at 1.5B,
judge-consistency report, capability matrix, consolidated project-plan doc.
See EXP-2026-07-03-001..003, F-2026-07-03-001..003, D-2026-07-03-003, TODO.md.
```

## CP-2026-07-04-001 - Overnight scale sweep + DPO + collapse ablation + citation first-run

Status:

```text
Overnight A100 session (2026-07-03 evening -> 07-04, GPU 0, env v0.3 test n=48,
oracle 0.8473, greedy seed 0; base SFT adapters from 07-03). Three nights of runs
written up and evidenced. HEADLINE: 3B is the sweet spot - 3B SFT alone hits gate
1.000 and 3B GRPO-v2 lands EXACTLY on the oracle (0.8473). Scale curve is
non-monotonic both ways. DPO and GRPO bracket the tradeoff (gate-perfect vs
reward-optimal). 0.5B collapse REPEATS despite mitigations (capacity floor,
sampling-vs-greedy split). Citation first-run is an honest negative (wrong action
space). All evidence in scripts/rl/runs/, weights git-excluded, manifests re-redacted.
```

Headline results (test @lambda=0.3, oracle 0.8473):

```text
SCALE CURVE (SFT reward / gate -> GRPO-v2 reward / gate):
  0.5B  0.6061/0.50  -> 0.383/0.00  COLLAPSE (greedy; samples keep gate alive)
  1.5B  0.7495/0.875 -> 0.7997/0.875  (+0.05, gate unchanged; oversample = null at 1.5B)
  3B    0.8428/1.000 -> 0.8473/1.000  = ORACLE; "SFT suffices at 3B" (kill +0.0045)
  7B    0.7147/0.75  -> 0.7997/0.875  (7B SFT non-monotonic DOWN; GRPO recovers)
DPO 1.5B (beta 0.1): 0.5382 / gate 1.000 / success 0.58 - gate-perfect, reward-collapsed
Citation 1.5B (n=31): prompted verdict_acc 0.2581 fab 0.871 -> GRPO verdict_acc 0.1935
  fab 0.742, cite_gold 0.0645 -> 0.1935 (3x); pre-registered bar failed (honest negative)
```

Evidence paths (postTrain, this repo; weights excluded by .gitignore):

```text
runs/grpo_v2_qwen15/20260703T1551Z-e571324/   (R1 oversample null; test_preds -> AMD_00 miss)
runs/dpo_qwen15/20260703T1607Z-e571324/  + runs/dpo_qwen15_pairs.jsonl  (R2 DPO)
runs/grpo_v2_qwen05/20260703T1608Z-e571324/   (R4 collapse repeat; parent 20260703T1507Z)
runs/sft_qwen3/20260703T1623Z-e571324/  runs/grpo_v2_qwen3/20260703T1624Z-e571324/  (3B, oracle)
runs/sft_qwen7/20260703T1646Z-e571324/  runs/grpo_v2_qwen7/20260703T1648Z-e571324/  (7B)
runs/citation_prompted15_test_eval.json  runs/grpo_citation15/20260703T1725Z-e571324/  (citation)
runs/gpu_session_20260703/{run_night,run_night2,run_night3}.sh, night*_batch.log
docs/PORTFOLIO_INDEX.md  (new interviewer front-door index)
```

Note: all 8 new run_manifest.json files had their tensorboard `logging_dir`
hostname suffix REDACTED to `_REDACTED` before commit, with the
`redaction_note` field added (same convention as 07-03). The 6 tracked 07-03
manifests were re-restored from HEAD after the overnight rsync reverted their
redaction. Per-run pip_freeze records the authoritative env (trl==0.15.2).

Resume:

```text
Morning human-review queue: rule on router_contract_realtool_risk_review_AMD_00
(gate up-front vs cheap-then-escalate acceptable) BEFORE any label change
(D-2026-07-04-003). Then: implement citation env v2 (letter-indexed A-F action
space, D-2026-07-04-002) and re-run 1.5B; DPO pair v2 with failed-to-escalate
negatives (D-2026-07-04-004); Gemma 4 cross-family arm (needs HF license + fresh
venv w/ Gemma4 transformers support); optional 0.5B temperature-sweep probe to
quantify the sampling-vs-greedy gap. See EXP/F/D-2026-07-04-*, TODO.
```

## CP-2026-07-04-002 - Rounds 3/4 wrap-up: multi-seed error bars, Gemma cross-family, citation SFT probe, R6 rescore

Status:

```text
Round-3 discussion items (F1/F2/F3) and batch-4 (Phases A/B/C) closed out and
written up with the honest revisions they forced. All evidence local under
training-corpus/scripts/rl/runs/; weights git-excluded. env v0.3.1 seed patch
created but NOT wired into the loader (opt-in only). R6 dual-convention rescore
done offline from dumped test_preds.
```

Headline results:

```text
ROUND 3:
  F1 citation LETTERS (1.5B, n=31): prompted fab 0.0 / cite_gold 0.742 / verdict 0.0968
    / reward 0.5452; GRPO fab 0.0 / cite_gold 0.871 / verdict 0.0968 / reward 0.571.
    Action-space CONFIRMED; verdict fell 0.258->0.097 (partly lucky-guess before);
    component decoupling. Bar HALF-met (honest partial).
  F2 DPO v2 (1.5B): reward 0.5213 / gate 1.000 / success 0.5833 - pair fix insufficient;
    next lever = beta sweep.
  F3 0.5B temp probe: T0.7 presence 0.0, T1.0 presence 0.25, per-sample gate 0.0625 <
    0.9 threshold -> collapse = genuine knowledge loss (capacity floor upgraded to tested).
BATCH 4:
  A SFT 1.5B reward@0.3 0.7024+/-0.0333 [0.6772,0.7495] (seed 0 best; "1.5B beats 7B"
    seed-0-only); GRPO-v2 3B 0.8473+/-0.0000 gate 1.000+/-0.0 (oracle x3, crown jewel);
    GRPO 0.5B 0.4721+/-0.1221 gate 0.1667+/-0.2357 (collapse 2/3 seeds, instability).
  B Gemma-4 E2B/E4B prompted 0.744/0.7452 gate 0.875 success 0.9375 - cross-family
    blindness REFUTED (family-dependent); Gemma-2.3B-eff ~ Qwen-7B prompted.
  C citation SFT-letters (1.5B, n=31) verdict_acc 0.0645 < prompted - SUPERVISED also
    fails verdict -> data-starved (62 rows), not RL's fault.
```

Evidence paths (postTrain, this repo; weights excluded by .gitignore):

```text
runs/citation_letters_prompted15_test_eval.json
runs/grpo_citation_letters15/20260704T0045Z-e571324/    (F1 GRPO-letters)
runs/dpo_v2_qwen15/20260704T0059Z-e571324/  + runs/dpo_v2_qwen15_pairs.jsonl  (F2)
runs/grpo_v2_qwen05/20260703T1608Z-e571324/{sampled_T0.7_eval.json,sampled_T1.0_eval.json}  (F3)
runs/agg/{sft_qwen15,grpo_v2_qwen3,grpo_qwen05}.json  (A aggregates, per-seed + mean/std)
runs/sft_qwen15_seed{1,2}/  runs/grpo_v2_qwen3_seed{1,2}/  runs/grpo_qwen05_seed{1,2}/  (A seeds)
runs/gemma_prompted/{e2b,e4b}_test_eval.json  {e2b,e4b}_test_preds.jsonl  (B)
runs/sft_citation15/20260704T0251Z-e571324/  (C citation SFT)
runs/r6_rescore_summary.json + scripts/analysis/rescore_r6.py  (R6 dual-convention rescore)
env_seeds_v0.3.1.json (next to v0.3, AMD_00 no-gate + gate_convention; loader NOT changed)
runs/gpu_session_20260704/{batch4.log,r3_batch.log}
docs/PORTFOLIO_INDEX.md  (full refresh)
```

Not rescoreable (no test_preds.jsonl dumped): seed-0 sft_qwen15, grpo_qwen15,
grpo_qwen05, sft_qwen05. Rescoreable: 14 runs (grpo_v2_qwen15, dpo, dpo_v2, sft/grpo_v2
3B x3 seeds, sft/grpo_v2 7B, grpo_qwen05 seed1/seed2, grpo_v2_qwen05, gemma e2b/e4b).

Resume:

```text
Next: wire env v0.3.1 only into NEW runs that opt in (loader preference order stays
("v0.3","v0.1") on purpose). Priority queue: citation corpus growth 131->300-500 then
re-run (verdict data-starvation); DPO beta sweep (F2 next lever); env v0.4 memory arm
construction (four-arm matrix, D-2026-07-03-002). Second tier: Plan C inference-backend
control column, lambda=0.6 exploration. See EXP/F/D-2026-07-04-004..009, TODO.
```

## CP-2026-07-04-003 - Round 5 wrap-up: DPO beta closure, citation data-scaling confirmed 6x

Status: superseded by CP-2026-07-04-004

```text
DPO escalation arm closed (over-conservatism STRUCTURAL across 2 pair designs x 3
betas). Citation data-starvation VALIDATED: SFT-letters on the class-balanced expanded
pool jumped verdict_acc ~6x on the frozen test. All three run dirs local under
training-corpus/scripts/rl/runs/; weights git-excluded. The infra hostname suffix in the
three new run_manifest.json logging_dir fields was REDACTED to _REDACTED per convention.
```

Headline results:

```text
DPO BETA SWEEP (1.5B, pairs v2, escalation @lambda0.3, greedy, test n=48):
  beta=0.1 (prior): reward 0.5213 / success 0.5833 / gate 1.000
  beta=0.3        : reward 0.5989 / success 0.6667 / cost 0.2258 / gate 1.000
  beta=0.5        : reward 0.5989 / success 0.6667 / cost 0.2258 / gate 1.000  (DIGIT-IDENTICAL to beta=0.3)
  vs SFT baseline 0.7495 -> plateaus ~15 pts below; kill line not re-crossed (delta -0.1506).
  => DPO safety-first is STRUCTURAL. Three-method FINAL: GRPO=efficiency, DPO=safety, SFT=balanced.
CITATION EXPANSION v1 (build, commit b6c909a): +146 construction-labeled rows (train 122/dev 24,
  no test), 21 AI issuers, 0 fetch fails, labels verified70/contradicts35/partial22/insufficient19
  (un-starves boundary classes), 93.3% blind spot-audit. Combined train pool 131+146=277.
D-008 DATA-STARVATION TEST (SFT-letters 1.5B on expanded pool, FROZEN test n=31, letters):
  verdict_acc 0.0645(@62) -> 0.3871(@expanded) ~6x; cite_gold 0.8387->0.9355; fabricated 0.0;
  mean_reward 0.5323->0.8742. HYPOTHESIS CONFIRMED - verdict head was class-starved.
  Chain complete: action-space(fixed) -> data(confirmed) -> capacity(next 3B probe).
  Caveats: 0.387 still far from usable; single seed; n=31; construction-labeled train.
```

Evidence paths (postTrain, this repo; weights excluded by .gitignore):

```text
runs/dpo_v2_beta03_qwen15/20260704T0624Z-e571324/  (beta=0.3; test_eval, metrics, manifest, preds, trainer_log)
runs/dpo_v2_beta05_qwen15/20260704T0626Z-e571324/  (beta=0.5, digit-identical greedy)
runs/sft_citation15_expanded/20260704T0647Z-e571324/  (D-008 payoff; citation_sft_expanded_test_eval.json)
.../citation_contract_repair_v0.1/citation_train_expansion_v1/  (dataset, commit b6c909a; manifest.json)
runs/gpu_session_20260704/{batch4.log,r3_batch.log}  (gitignored, not committed)
docs/PORTFOLIO_INDEX.md  (citation attribution-chain + three-method table refresh)
```

Log ids this round: EXP-2026-07-04-010 (beta sweep), -011 (expansion build backfill),
-012 (data-starvation test); D-2026-07-04-009 (data-scaling validated + DPO structural);
CP-2026-07-04-003. No new FAILURE entry (beta-identical policies is an EXPERIMENT
observation).

Resume:

```text
Next queue: citation collection batch 2 -> ~400+ (277 today); 3B citation SFT capacity
probe on the expanded pool; GRPO-letters on the expanded pool (does RL add over healthy
SFT data). Standing big-ticket: env v0.4 memory-arm construction (four-arm matrix,
D-2026-07-03-002/005). Second tier: Plan C inference-backend control column, lambda=0.6
exploration arm, full SFT+GRPO seed-varied 3B. See EXP/D-2026-07-04-010..012, TODO.
```

## CP-2026-07-04-004 - Round 6 wrap-up: citation chain CLOSED (capacity null, RL null, data is the lever)

Status: prior

```text
Citation attribution chain CLOSED end to end. Two clean negatives ran the last two links
on the SAME frozen test (n=31, letters), everything else held fixed: (a) 3B on the
IDENTICAL 122-row expanded pool is WORSE than 1.5B -> capacity is not the verdict lever;
(b) GRPO-letters from the expanded-SFT adapter is DIGIT-IDENTICAL to its SFT init on
every test metric -> RL adds 0.0 on healthy SFT data. Fabrication was fixed by
ACTION-SPACE, the verdict by DATA BALANCE; neither by capacity, neither by RL. Founding
"do we need RL" question answered TASK-DEPENDENTLY. Both new run dirs local under
training-corpus/scripts/rl/runs/; weights git-excluded. The infra hostname suffix in the
two new run_manifest.json logging_dir fields was REDACTED to _REDACTED per convention
(redaction_note appended).
```

Headline results:

```text
CAPACITY PROBE (3B citation SFT-letters, expanded pool, FROZEN test n=31, letters):
  1.5B (EXP-...-012): verdict_acc 0.3871 / cite_gold 0.9355 / fabricated 0.0 / reward 0.8742
  3B   (this)       : verdict_acc 0.2903 / cite_gold 0.9032 / fabricated 0.0 / reward 0.7710
  => 3B WORSE than 1.5B on identical data; capacity NOT the bottleneck at 122 rows. CLOSED.
RL-INCREMENT ON HEALTHY DATA (GRPO-letters 1.5B from expanded-SFT init, 300 batches, test n=31):
  verdict_acc 0.3871 / cite_gold 0.9355 / cite_valid 1.000 / fabricated 0.0 / reward 0.8742
  => DIGIT-IDENTICAL to SFT init on every metric. Train-time batch verdict_acc ~0.94 (train
  saturation) but greedy test policy unchanged => RL increment = 0.0. One train-time
  "<label>" template artifact in reward_trace verdict_mix (not in test outputs; minor).
TASK-DEPENDENT RL TABLE (RL over SFT, same frozen eval):
  escalation 1.5B: +4.9 pts (0.7495 -> 0.7997); escalation 3B: +0.45 (0.8428 -> 0.8473 oracle);
  citation verdict 1.5B: +0.0 (digit-identical). "Not RL for RL's sake" is now empirical.
  Caveats: both probes single-seed, n=31, construction-labeled train; directional negatives.
```

Evidence paths (postTrain, this repo; weights excluded by .gitignore):

```text
runs/sft_citation3b_expanded/20260704T0658Z-e571324/    (capacity probe; citation_sft3b_test_eval.json, metrics, manifest, trainer_log)
runs/grpo_citation15_postexp/20260704T0659Z-e571324/    (RL-increment; citation_grpo_postexp_test_eval.json, metrics, manifest, trainer_log, reward_trace, generations)
docs/PORTFOLIO_INDEX.md    (citation section COMPLETE + task-dependent RL table)
```

Log ids this round: EXP-2026-07-04-013 (capacity probe), -014 (RL-increment);
D-2026-07-04-010 (task-dependent RL synthesis + chain closed); CP-2026-07-04-004. No new
FAILURE entry (both are clean negatives / EXPERIMENT observations; the "<label>" artifact
is a minor train-side note, not a failure).

Resume:

```text
Citation line CLOSED pending data batch-2 (277 -> ~400+); no further capacity/RL tuning on
the current 122-row pool (a larger N may re-open capacity at 400+, not at 122). Queue in
order: citation collection batch 2 -> ~400+; env v0.4 memory-arm construction (four-arm
matrix, D-2026-07-03-002/005, standing big-ticket). Second tier: Plan C training-free /
inference-backend GRPO, lambda=0.6 exploration arm, full SFT+GRPO seed-varied 3B. See
EXP/D-2026-07-04-013..014, D-2026-07-04-010, TODO.
```

## CP-2026-07-04-005 - Round 7 wrap-up: full-FT probes - 0.5B GRPO collapse REATTRIBUTED to adapter capacity; LoRA protective at 7B

Status: superseded by CP-2026-07-04-006 (the 7B "LoRA protective" reading is amended - it was an lr artifact; E1b hits exact oracle)

```text
Full-parameter fine-tuning probes at both ends of the model range, same 160 rows / same
frozen escalation test (n=48, lambda=0.3, oracle 0.8473), toggling ONLY trainable-parameter
budget (LoRA r=16 -> full). They reverse in OPPOSITE directions and yield one principle:
"trainable-parameter budget must match data size." At 0.5B, full-FT RESCUED GRPO from the
collapse (0.383/gate 0.00 -> 0.7533/gate 0.75, NO collapse) => the 0.5B GRPO collapse is
REATTRIBUTED from a model-capacity floor to an ADAPTER-capacity floor (LoRA r=16). At 7B,
full-FT DESTROYED it (0.7147 -> 0.5079, -20.7 pts) => LoRA is a REGULARIZER at 7B on tiny
data. Campaign's SECOND self-correction (first: multi-seed 1.5B downgrade). Kill bar
unchanged (0.5B full gate 0.75 < 0.99, not deployable). All probes single-seed (seed 0).
7B run completed only after a 3-attempt OOM chain around a ~34GB coexisting non-ours GPU
process (ownership escalated to owner, pending). New run dirs local under
training-corpus/scripts/rl/runs/; weights git-excluded. The infra hostname suffix
(hostname suffix) in the 5 new run_manifest.json logging_dir fields was REDACTED to _REDACTED
per convention (redaction_note appended). Origin: owner's parameterization question
"我们的RL做的也是LoRA?…可以尝试全量微调嘛?".
```

Headline results:

```text
E2 - 0.5B FULL-FT (frozen test n=48):
  full-SFT 0.5B : reward 0.5899 / gate 0.75  (LoRA-SFT was 0.6061 / 0.50 - reward ~same, gate BETTER)
  full-GRPO 0.5B (from full-SFT init): reward 0.7533 / gate 0.75  (+14.7 over 0.6061 LoRA-SFT baseline)
    vs LoRA-GRPO 0.383 / gate 0.00 (collapsed 2/3 seeds). NO COLLAPSE.
  => collapse REATTRIBUTED to adapter capacity (LoRA r=16), not model capacity. Kill bar still not passed (0.75 < 0.99).
E1 - 7B FULL-FT SFT (frozen test n=48):
  full-SFT 7B : reward 0.5079 / gate 0.75  vs LoRA-SFT-7B 0.7147  => 20.7 pts WORSE.
  Pre-registered bar "full beats LoRA by >=3 -> LoRA binding" NOT met; INVERTED.
  => LoRA is a REGULARIZER at 7B / 160 rows. CONFOUND: lr NOT retuned (same 2e-4 default; full FT wants ~10x lower).
     Rigorous claim: "full FT at unchanged hyperparameters is much worse." E1b (low-lr sweep) pre-registered OPTIONAL.
UNIFIED: "trainable-parameter budget must match data size." 0.5B needed MORE (full rescued GRPO);
  7B needed LESS (full destroyed it). LoRA = bottleneck at small end, regularizer at large end - not a cost compromise.
  Caveats: both probes single-seed (seed 0); LoRA-GRPO collapse baseline was 2/3 seeds; directional reattributions.
INFRA: 7B OOM chain - attempt1 batch8/accum2 OOM (44.7GB ours + 34.16GB neighbor); attempt2 batch4/accum4 OOM by ~800MB;
  attempt3 batch2/accum8 + expandable_segments SUCCEEDED. Coexisting compute_capture.py (deepseek/confiqa, ~34GB,
  same account not ours) discovered on GPU 0, NOT touched; footprint shrunk to coexist. Ownership escalated (pending).
```

Evidence paths (postTrain, this repo; weights excluded by .gitignore):

```text
runs/fullsft_qwen05/20260704T0752Z-e571324/    (E2 full-SFT 0.5B; fullsft_test_eval.json, metrics, manifest, test_preds, trainer_log)
runs/fullgrpo_qwen05/20260704T0753Z-e571324/   (E2 full-GRPO 0.5B; fullgrpo_test_eval.json, metrics, manifest, test_preds, trainer_log, reward_trace, generations)
runs/fullsft_qwen7/20260704T0805Z-e571324/     (E1 successful full-SFT 7B; fullsft7b_test_eval.json, metrics, manifest, test_preds, trainer_log; --parent-run 20260704T0801Z)
runs/fullsft_qwen7/20260704T0801Z-e571324/     (E1 OOM attempt 1, manifest-only)
runs/fullsft_qwen7/20260704T0804Z-e571324/     (E1 OOM attempt 2, manifest-only)
docs/FAILURE_TAXONOMY_GRPO_COLLAPSE.md         (top addendum line: reattribution pointer)
docs/PORTFOLIO_INDEX.md                        (0.5B collapse reattribution + parameterization-budget finding)
```

Log ids this round: EXP-2026-07-04-015 (0.5B full-FT, reattribution), -016 (7B full-FT,
LoRA-as-regularizer); F-2026-07-04-007 (7B OOM chain + neighbor process); D-2026-07-04-011
(parameterization-budget synthesis + reattribution + E1b optional); CP-2026-07-04-005.

Resume:

```text
Full-FT probe line DONE (E2 reattribution + E1 reversal + unified synthesis). Optional
follow-ups: E1b (lower-lr full-FT 7B sweep - fair test of the lr confound); seed-varied
full-GRPO-0.5B to harden the non-collapse. Neighbor GPU-process (compute_capture.py ~34GB)
ownership question PENDING owner. Standing queue unchanged: citation collection batch-2
(277 -> ~400+); env v0.4 memory-arm construction (four-arm matrix, big-ticket). Second tier:
Plan C inference-backend GRPO, lambda=0.6 exploration arm, full seed-varied 3B. See
EXP/D-2026-07-04-015..016, D-2026-07-04-011, TODO.
```

## CP-2026-07-04-006 - Round 8: E1b - 7B full-FT at a PROPER lr hits EXACT ORACLE; the E1 "20.7 pts worse / LoRA regularizes at 7B" verdict was an lr artifact

Status: current

```text
E1b is the pre-registered fair test of the E1 lr confound. It re-ran the 7B full-SFT arm
changing ONLY the learning rate (2e-4 -> 2e-5; 2e-4 is a LoRA-standard lr, catastrophic for
7B full-param), identical to E1 in every other respect (same model, same 160 rows, same
frozen escalation test n=48, lambda=0.3, oracle 0.8473, seed 0), on a free GPU (no OOM chain
this time; batch 8 / accum 2). Result: reward 0.5079 -> 0.8473 = EXACT ORACLE, gate_recall
1.000, +13.3 over LoRA-7B-SFT (0.7147). SECOND config ever to solve the env (first: GRPO-v2
3B x3 seeds). The pre-registered E1 bar "full beats LoRA by >=3 -> LoRA was binding" is now
MET. Campaign self-correction #4, and it corrects #3 (the E1/D-011 "LoRA protective at 7B"
half). The 0.5B adapter-floor reattribution (E2) STANDS - it was full-FT at the SAME lr that
fixed it. Revised synthesis: hyperparameters must be matched to the parameterization;
shared-lr LoRA-vs-full comparisons are confounded by construction. The scale-curve 7B dip is
reinterpreted from "capability/data ceiling" to "config artifact." New manifest logging_dir
hostname suffix REDACTED to _REDACTED per convention (redaction_note appended). Single seed;
3B (LoRA-GRPO, 3 seeds) remains the strongest REPLICATED result. Origin: owner's prompts
drove this entire probe line.
```

Headline results:

```text
E1b - 7B FULL-FT SFT, PROPER lr (frozen test n=48):
  full-SFT 7B @ lr 2e-5 : reward 0.8473 / gate 1.000 / success 1.0  == EXACT ORACLE (0.8473)
  chain (only lr changed): 2e-4 full -> 0.5079 ; 2e-5 full -> 0.8473 ; LoRA-7B-SFT -> 0.7147
  kill_check lambda0.3: 0.8473 vs baseline 0.7147, delta +0.1326, beats_by_3pts_and_holds_gate = TRUE
  (reward: lambda0.1 0.9491 / lambda0.6 0.6945; gate 1.000 at all lambdas)
  => E1 "20.7 pts worse / LoRA regularizes at 7B" = lr artifact. Pre-registered bar MET (+13.3).
  => Env now solved by TWO configs: 3B LoRA-GRPO (3 seeds, zero variance) + 7B full-SFT (single seed).
```

Evidence paths (postTrain, this repo; weights excluded by .gitignore):

```text
runs/fullsft_qwen7_lowlr/20260704T1157Z-e571324/   (E1b; fullsft7b_lowlr_test_eval.json, metrics, manifest, test_preds, trainer_log; --parent-run 20260704T0805Z-e571324)
DECISIONS.md D-2026-07-04-011                       (dated amendment appended in place)
DECISIONS.md D-2026-07-04-012                       (the amendment: revised synthesis + per-arm-tuning lesson)
docs/PORTFOLIO_INDEX.md                             (finding #9 reframed; scale-curve "7B dip = config artifact"; env solved by two configs)
```

Log ids this round: EXP-2026-07-04-017 (E1b, 7B full-FT proper lr = exact oracle);
D-2026-07-04-012 (amendment to D-2026-07-04-011 + per-arm-tuning lesson); CP-2026-07-04-006.

Resume:

```text
E1b DONE - 7B full-FT at proper lr (2e-5) hits exact oracle (0.8473 / gate 1.000, +13.3 over
LoRA); the E1 lr confound is resolved and D-011's 7B half amended (D-012). Env solved by two
configs (3B LoRA-GRPO replicated; 7B full-SFT single-seed). Optional, NOT committed: E1b seed
replication; LoRA-7B lr sweep. Standing queue unchanged: citation collection batch-2
(277 -> ~400+); env v0.4 memory-arm construction (four-arm matrix, big-ticket). Second tier:
Plan C inference-backend GRPO, lambda=0.6 exploration arm, full seed-varied 3B. See
EXP-2026-07-04-017, D-2026-07-04-012, D-2026-07-04-011, TODO.
```
