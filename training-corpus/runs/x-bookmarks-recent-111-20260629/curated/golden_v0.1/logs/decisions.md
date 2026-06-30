# Golden v0.1 Decisions

Timestamp: 2026-06-29T06:41:57.341772+00:00

## Decisions

- Freeze `strict_pilot_trace_25` as the v0.1 golden source before generating more data.
- Keep runtime DB and training corpus separate.
- Expand router with synthetic scenario templates because router needs coverage across workflow types, not just market narratives.
- Expand citation verifier using mismatched-span and missing-evidence negatives, clearly labeled as synthetic.
- Expand risk reviewer with deterministic high/medium/low scenarios because the strict pilot alone is too sparse for risk boundaries.
- Do not create a `calculation_verifier` model dataset here; deterministic math/code should handle calculations first.
- Iteration bug fixed: initial freeze copy used only basename, so multiple `all.jsonl` inputs collided. Freeze filenames now include relative path segments.
- Iteration safety fix: golden-pack regeneration now clears only managed outputs, preserving child pilots such as `real_tool_trace_pilot_10`.

## Known Limitations

- Synthetic rows are for cold start only; they must be replaced or audited with real user queries and real tool traces.
- Citation verifier still needs more real paragraph-level official/filing/press-release spans.
- Router labels need online evaluation later: over-trigger, under-trigger, latency, cost, and safety recall.
- Risk reviewer labels encode policy, not user preference. User preference cannot override safety/compliance boundaries.

## Counts Snapshot

- `router_classifier`: 344 rows, splits={'train': 249, 'dev': 47, 'test': 48}, labels={'evidence_check': 67, 'deep_research': 53, 'fast_answer': 90, 'risk_review': 30, 'price_lookup': 26, 'news_retrieval': 26, 'clarification_needed': 26, 'financial_calculation': 26}
- `citation_verifier`: 166 rows, splits={'train': 108, 'dev': 27, 'test': 31}, labels={'partial_support': 27, 'supports': 40, 'contradicts': 4, 'not_supported': 75, 'insufficient': 20}
- `risk_reviewer`: 181 rows, splits={'train': 121, 'dev': 23, 'test': 37}, labels={'high': 83, 'medium': 69, 'low': 29}
