#!/usr/bin/env python3
"""SpanCase dataclass shared by the expansion builder and its cases module.

Kept in a tiny standalone module so `citation_train_expansion_v1_cases.py` can
import the dataclass without importing the builder (which imports the cases),
avoiding a circular import.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpanCase:
    case_key: str
    source_key: str
    anchor: str
    claim: str
    support_type: str
    claim_scope: str
    section: str
    rationale: str
    split: str                         # "train" or "dev" ONLY
    must_contain: tuple[str, ...] = ()
    point_in_time_allowed: bool = True
