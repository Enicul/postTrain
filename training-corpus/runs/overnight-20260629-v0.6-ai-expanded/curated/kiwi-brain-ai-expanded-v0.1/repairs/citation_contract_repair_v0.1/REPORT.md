# citation_contract_repair_v0.1

## Why

The current citation verifier mixes two different concepts:

- evidence retrieval: "this source might be relevant";
- citation verification: "this exact span supports this exact claim".

That ambiguity makes the model over-accept topical evidence. For KIWI, this is
dangerous because a final memo can look well-cited while the cited span only
supports a weaker or adjacent claim.

## Contract

Use five support labels:

| Label | Meaning | Can support final memo? |
| --- | --- | --- |
| `candidate_evidence` | Relevant enough to inspect, support not verified | No |
| `verified_support` | Direct span-level support under point-in-time constraints | Yes |
| `partial_support` | Supports only part of a composite claim or a weaker claim | No |
| `insufficient` | Topical/adjacent but not enough for the claim | No |
| `contradicts` | Conflicts with or weakens the claim | No |

## Required Fields

Each row should store:

```json
{
  "claim": "...",
  "evidence_span": "...",
  "source_url": "...",
  "source_class": "official / filing / press_release / transcript / news / social / analyst",
  "as_of": "YYYY-MM-DD",
  "support_type": "candidate_evidence | verified_support | partial_support | insufficient | contradicts"
}
```

Optional but useful:

```json
{
  "evidence_id": "...",
  "evidence_title": "...",
  "claim_scope": "single_fact / composite / thesis / risk / forward-looking",
  "ticker": "...",
  "captured_at": "...",
  "published_at": "...",
  "point_in_time_allowed": true
}
```

## Mapping Rules

- A headline can be `candidate_evidence`, but should not become
  `verified_support` for a financial thesis unless the headline itself is the
  claim being verified.
- A social/X/Weibo/XHS post is opinion evidence. It can seed a task, but it is
  not final support unless another auditable source backs it.
- Composite claims need subclaim coverage. If the span supports revenue growth
  but not margin or guidance, label it `partial_support`.
- If a source is after the decision `as_of`, label it as leakage and exclude it
  from verified support.
- `contradicts` rows should be preserved as risk evidence, not thrown away.

## Decision

Do not train `citation_verifier_repair_v0.3` yet. First collect real paragraph
spans from official IR/SEC/press-release/transcript/news pages and label them
under this contract.
