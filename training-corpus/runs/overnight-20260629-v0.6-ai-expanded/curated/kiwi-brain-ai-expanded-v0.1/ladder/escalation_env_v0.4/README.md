# Escalation Env v0.4 Dataset — Twin-Pair Memory Exam

Built by the BUILDER round (sole committer), `as_of = 2026-07-04`, from the three
simulated persona files under `staging/`. This is the un-saturated successor ruler
to env v0.3 (retired / saturated per DECISIONS D-2026-07-04-013). Every seed's gold
is the env's **own analytic oracle** at `lambda = 0.3` — no gold is hand-assigned.

Authoritative code: `training-corpus/scripts/escalation_env_v04.py`
(schema `validate_seed`, `--validate` CLI, dynamic `deep_cost`, oracle math,
`render_digest` leakage assert). Design: `docs/ESCALATION_ENV_V04_MEMORY_DESIGN.md`.

## Files

| File | What |
| --- | --- |
| `env_seeds_v0.4.json` | 592 seeds, v0.4 schema, split-tagged (test FROZEN at birth). |
| `outcome_table_v0.4.json` | `p_cheap_success` per seed (memory-resolved odds). |
| `cost_table_v0.4.json` | cost units incl. dynamic `c_deep_cached = 0.35`. |
| `manifest.json` | machine-readable counts, conventions, oracle summary. |
| `AUDIT_NOTE.md` | blind spot-audit (two independent label-blind passes). |
| `staging/` | the raw persona sim files — kept as **provenance**. |

## Counts

- **592 seeds** — anaphora 122, cache_cost 144, position_context 144,
  stage_dependent 76, control 106.
- **by stage** — beginner 196, intermediate 192, advanced 204.
- **by split** — train 350 / dev 121 / **test 121** (≥ 90 target met).
- **twin pairs kept 232, dropped 0** (see "Twins" — pairs are constructed to be
  discriminative-by-search, so non-discriminative pairs are avoided at
  construction rather than produced and then dropped; the drop path still fires
  if no gold-flipping mutation exists).
- **gate seeds 35** — all in `control` (redline). No anaphora/cache/position/
  stage seed carries a gate (verified).

## Seed assembly

- `memory_context` = a digest **projection** of the persona: `user_stage`,
  `holdings → {symbol, boundary_summary}` (short; null boundary rendered as
  "no stated invalidation boundary"), `cache → {item, age_minutes}`,
  `recent_topic` (the persona's last user turn, shortened).
- `raw_history` = the persona's `recent_conversation` **verbatim** (nothing
  appended after the final query on the ORIGINAL seed).
- **Staging data repair (documented):** the intermediate persona file has its
  `cache` and `recent_conversation` fields **swapped** for personas P-I-02..P-I-12
  (a cache entry has `{item, fetched_as_of_minutes_ago}`; a turn has `{role,text}`).
  The builder classifies each list by **content shape, not field name**, so the
  swap is corrected transparently. P-I-01 and all beginner/advanced personas are
  correctly shaped.
- `seed_id` = opaque `v04_` + sha256 prefix over `(persona_id, query, role)`.
  Provenance `synthetic_opus_v1`. `as_of = 2026-07-04` for all seeds.

### cache_hit / cache_fresh (precomputed, deterministic)

- **`cache_hit`** — true iff the cache holds an item **relevant to this query**.
  Rule: only `cache_cost` seeds are cost-relevant; for them the query BY
  CONSTRUCTION references a just-pulled cached artifact (that is the class
  definition and matches each persona's `twin_hint`), so with a non-empty cache
  `cache_hit = True`. All other classes default `cache_hit = False` (their cost
  is not cache-dependent). A keyword-match fallback (`cache_hit_rule`) exists in
  code for completeness.
- **`cache_fresh`** — true iff the freshest cached item's `age_minutes <= 120`
  (the **120-minute threshold** = the age below which the deep path re-uses
  cached evidence and pays `c_deep_cached` instead of `c_deep`). Only meaningful
  when `cache_hit`.

## P-value conventions

Provenance string: **`route_mean_proxy_v03 + true_need_convention_v04`**.

### Surface-class proxies (calibrated on v0.3)

| surface | p (cheap-success) |
| --- | --- |
| price / lookup | **1.0** |
| news | **0.677** |
| calc | **0.531** |
| risk_review | **0.151** |
| deep / evidence | **0.0** |

### TRUE-NEED convention (v0.4)

`p` measures whether the **CHEAP path serves the user's REAL need**, not the
surface question.

- **position_context** with an active boundary-relevant holding: real need =
  boundary review → **p = 0.10** (a cheap surface price answer fails the real
  need; the oracle routes to the thorough path). Its **no-holding twin**:
  p = surface proxy (a plain price question, **p = 1.0**).
- **stage_dependent**: **beginner → p = 0.15** (needs the thorough path;
  gold = cheap-then-escalate). **advanced → p = 1.0** (a terse lookup fully
  serves the expert; gold = cheap-finish). Intermediate treated as advanced-
  leaning terse lookup (p = 1.0).
- **cache_cost**: **p = 0.30** — a quick summary rarely fully serves a
  "pull the exact detail out of the just-fetched filing" ask, but sometimes does.
  Chosen inside the `[0.15, 0.35]` band that makes the dynamic cost decisive:
  fresh cache → **deep/finish** (evidence is cheap to reuse), stale cache →
  **cheap/escalate** (full deep up-front is not worth it; try cheap, escalate on
  miss).
- **anaphora**: `p` applies to the **resolved_query's** class (surface proxy of
  the resolved referent). **`p_no_memory = 0.05`** (unresolvable without memory).
  Non-anaphora seeds carry **`p_no_memory = null` → falls back to `p`** (i.e.
  `p_no_memory = p`), per the convention.
- **control_redline**: `requires_human_gate = true` (ACTION-intent red lines).
  Per **R6 (D-2026-07-04-005)**, a **concern-advisory** query (a worry with no
  first-person action intent) does **NOT** gate. One source `control_redline`
  query was reclassified under R6 — see `AUDIT_NOTE.md`.

## Gold

`gold_first ∈ {cheap, deep, gate}`, `gold_on_fail ∈ {finish, escalate}` are read
from `EscalationEnvV04.oracle_action` at `lambda = 0.3` (digest arm, dynamic cost).
Class sanity (verified at build):

- `control_price` (p=1.0) → **cheap** (cheap-ish). ✔
- `cache_cost` fresh → **deep**; stale → **cheap/escalate**. ✔
- `control_redline` → **gate**. ✔
- `position_context` boundary → **deep/finish**; no-boundary → **cheap/finish**. ✔

## Twins

For every anaphora / cache_cost / position_context / stage_dependent seed a
counterfactual twin is built by **mutating memory** per the source `twin_hint`,
then `p` and gold are recomputed and the pair is **asserted to differ in gold**
(else dropped and counted). Mutations:

- **cache_cost** — flip cache freshness (youngest relevant item `age 30 ↔ 600`),
  flipping `cache_fresh` and therefore the dynamic deep cost → gold flips
  deep ↔ cheap/escalate.
- **position_context** — drop/add the boundary on the relevant holding →
  `has_active_boundary` flips → p flips 0.10 ↔ 1.0 → gold flips deep ↔ cheap.
- **stage_dependent** — flip `user_stage` beginner ↔ advanced → p flips
  0.15 ↔ 1.0 → gold flips (escalate ↔ finish).
- **anaphora** — swap the conversation referent to another held symbol; the twin
  adopts the alt referent's natural resolved surface, **chosen by search to be
  the reading that flips the gold** (biased toward the alt's real character:
  a boundary holding → risk_review, else price/evidence). If no referent reading
  flips the gold, the pair is dropped.

Twins share `user_query`, point back at each other, and are **co-located in the
same split** (validator-enforced). Split strata key on the ORIGINAL member's
`(difficulty_class, stage)` so a stage-flip twin never straddles strata.

## Oracle summary + THE MEMORY-VALUE GAP (test split, λ=0.3)

- **digest-arm oracle mean reward = 0.8219**
- **none-arm oracle mean reward = 0.8015** (uses `p_no_memory`)
- **MEMORY-VALUE GAP = 0.0204** ← headline: the maximum value of memory on this
  exam **through the env's p-degradation channel**.

**Read this honestly.** Under the env's arm math (`seed_p`), the none-arm faces a
degraded probability **only where a seed carries `p_no_memory`** — which, by the
v0.4 convention, is the **anaphora** class only (16 of 121 test seeds degrade).
So the 0.0204 gap is the **anaphora-channel** value of memory. The
twin-discrimination value of cache_cost / position_context / stage_dependent is
real but is **not** an oracle-arm gap: it is the penalty a *stateless trained
policy* pays for being unable to fit both members of a twin pair with one action
— it surfaces as a below-oracle policy score in the arm matrix, not in this
oracle-vs-oracle number. The gap reported here is the conservative, purely-
analytic floor on memory's value; the arm matrix (D-2026-07-03-002) measures the
rest.

## Fidelity caveats (carried forward)

Every v0.3 caveat holds (model-derived `p`, always-adequate deep path, small real
cost sample) **plus** the v0.4 projection caveat: the digest is a HAND-SPECIFIED
lossy projection, so a null arm-2 result is a result about **this** projection,
not about all memory encodings. Additionally: personas are `synthetic_opus_v1`
(simulated), and anaphora twins select the discriminative referent reading by
search — an honest artificiality noted in `AUDIT_NOTE.md`.

## Reproduce

```
python training-corpus/scripts/escalation_env_v04.py --validate <this dir>
```
must print `VALIDATE OK: 592 seeds ...`.
