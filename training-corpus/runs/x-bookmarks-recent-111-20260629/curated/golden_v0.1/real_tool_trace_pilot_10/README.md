# Real Tool Trace Pilot 10

This pilot runs real KIWI read-only provider calls: market quote, news RSS, and SEC EDGAR filings.
It does not write to the runtime database and does not execute trades.

## Counts

- Traces: 10
- Tool calls: 30
- Observation spans: 59
- Verdicts: {'complete_tool_trace': 8, 'partial_tool_trace': 2}
- Tool status: {'market_price_lookup:ok': 10, 'news_search:ok': 10, 'sec_edgar:ok': 10}
- Errors: 0

## Why This Matters

The earlier strict pilot proves claim-verification schema. This pilot proves the agent can actually call live research tools and preserve observations/errors as trace data.
