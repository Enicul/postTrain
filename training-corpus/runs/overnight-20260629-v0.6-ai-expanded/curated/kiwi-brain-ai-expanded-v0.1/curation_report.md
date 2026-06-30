# KIWI Brain Curated Pack: kiwi-brain-ai-expanded-v0.1

Source run: `/Users/lucine/Documents/Job/projects/Agent/kiwi/training-corpus/runs/overnight-20260629-v0.6-ai-expanded`

- Deterministic curation pass; no LLM calls.
- Chronological split from source run is preserved.
- Rows are deduplicated by task/input key and balanced by label family where possible.
- High-signal rows are preferred for risk, memo, SFT, DPO, and GRPO datasets.
- Router rows are rebuilt from tasks/all.jsonl with as_of and symbol context to avoid date-free template leakage.
- Citation verifier rows are augmented with synthetic mismatched and missing-evidence negatives.
- High-risk router rows are normalized to require a human gate, based on Claude brain audit feedback.

## Dataset Counts

### `router_classifier`
- `train`: raw `80535`, deduped `80535`, selected `6000`, duplicates `0`
- `dev`: raw `17641`, deduped `17641`, selected `1200`, duplicates `0`
- `test`: raw `16874`, deduped `16874`, selected `1200`, duplicates `0`

### `event_extractor`
- `train`: raw `39757`, deduped `39757`, selected `6000`, duplicates `0`
- `dev`: raw `10163`, deduped `10163`, selected `1200`, duplicates `0`
- `test`: raw `9799`, deduped `9799`, selected `1200`, duplicates `0`

### `citation_verifier`
- `train`: raw `73837`, deduped `73837`, selected `6000`, duplicates `0`
- `dev`: raw `19374`, deduped `19374`, selected `1200`, duplicates `0`
- `test`: raw `18703`, deduped `18703`, selected `1200`, duplicates `0`

### `calculation_verifier`
- `train`: raw `6195`, deduped `4248`, selected `2000`, duplicates `1947`
- `dev`: raw `1357`, deduped `944`, selected `500`, duplicates `413`
- `test`: raw `1298`, deduped `885`, selected `500`, duplicates `413`

### `risk_reviewer`
- `train`: raw `252974`, deduped `198200`, selected `8000`, duplicates `54774`
- `dev`: raw `58322`, deduped `43424`, selected `1600`, duplicates `14898`
- `test`: raw `55942`, deduped `41536`, selected `1600`, duplicates `14406`

### `memo_quality_scorer`
- `train`: raw `252974`, deduped `198200`, selected `8000`, duplicates `54774`
- `dev`: raw `58322`, deduped `43424`, selected `1600`, duplicates `14898`
- `test`: raw `55942`, deduped `41536`, selected `1600`, duplicates `14406`

### `sft_trajectories`
- `train`: raw `126487`, deduped `126487`, selected `8000`, duplicates `0`
- `dev`: raw `29161`, deduped `29161`, selected `1600`, duplicates `0`
- `test`: raw `27971`, deduped `27971`, selected `1600`, duplicates `0`

### `preference_pairs`
- `train`: raw `126487`, deduped `126487`, selected `8000`, duplicates `0`
- `dev`: raw `29161`, deduped `29161`, selected `1600`, duplicates `0`
- `test`: raw `27971`, deduped `27971`, selected `1600`, duplicates `0`

### `grpo_rollouts`
- `train`: raw `126487`, deduped `126487`, selected `8000`, duplicates `0`
- `dev`: raw `29161`, deduped `29161`, selected `1600`, duplicates `0`
- `test`: raw `27971`, deduped `27971`, selected `1600`, duplicates `0`

