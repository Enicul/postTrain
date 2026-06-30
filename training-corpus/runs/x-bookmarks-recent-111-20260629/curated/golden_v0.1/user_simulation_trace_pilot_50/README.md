# User Simulation Trace Pilot 50

This pilot simulates user inputs, routes them through a deterministic KIWI coordinator boundary, runs read-only tools when needed, and records blockers.

## Counts

- Traces: 50
- Tool calls: 77
- Observation spans: 159
- Blockers: 18
- Verdicts: {'partial_or_blocked': 11, 'complete': 32, 'needs_clarification': 7}
- Routes: {'fast_answer': 8, 'price_lookup': 7, 'news_retrieval': 7, 'evidence_check': 7, 'deep_research': 7, 'risk_review': 7, 'clarification_needed': 7}
- Blocker types: {'registry_tool_suggestion_overbroad': 15, 'missing_news_observation': 3}

## Interpretation

These are not final answers. They are episode-level traces for finding where KIWI gets stuck: routing, source availability, citation quality, risk gating, or tool behavior.
