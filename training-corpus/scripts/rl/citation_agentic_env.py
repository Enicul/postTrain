#!/usr/bin/env python3
"""Plan B: citation evidence-chain agentic environment (scaffold).

A genuinely multi-step, machine-checkable episode built on the audited
citation corpus (citation_real_eval_v1):

  state    : a claim (+ as_of, source_type)
  corpus   : the pool of audited evidence spans, addressed by evidence_id
  action   : the policy emits, in ONE generation (TRL-compatible flattening):
               {"cite": "<evidence_id>", "verdict": "<five-way label>"}
             i.e. RETRIEVE a span by id, then JUDGE support.
  reward   : process + outcome, all machine-checkable
     process : +0.3 if cited evidence_id exists in the pool
               -1.0 if the cited id is FABRICATED (not in the pool)  <-- the
                     hallucinated-citation hard negative
               +0.2 extra if the cited span is the one paired with the claim
     outcome : +1.0 if verdict == audited label, else 0.0
     (paragraph-hash check available for verbatim-quote variants)

This is the minimal same-shape version of the Kimi-Researcher evidence-chain
reward registered in LEARNING_SOURCES: reward the CHAIN (valid citation), not
just the final label.

Status: SCAFFOLD. Training needs the corpus grown to 300-500 rows (collector
proven at ~100/night). This module provides the reward + pool so a GRPO run
can plug in exactly like grpo_escalation.py once data lands.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FIVE_WAY = {"verified_support", "partial_support", "insufficient",
            "contradicts", "candidate_evidence"}


class CitationAgenticEnv:
    def __init__(self, eval_dir: Path):
        rows = [json.loads(l) for l in (eval_dir / "rows/all.jsonl").read_text().splitlines() if l.strip()]
        self.claims = {}          # claim_id -> {claim, gold_evidence_id, gold_label, split, ...}
        self.pool = {}            # evidence_id -> span text
        self.paragraph_hash = {}  # evidence_id -> hash
        for r in rows:
            cid = r["sample_id"]
            eid = r["input"]["evidence_id"]
            self.claims[cid] = {
                "claim": r["input"]["claim"], "as_of": r["input"].get("as_of"),
                "source_type": r["input"].get("source_type"),
                "gold_evidence_id": eid, "gold_label": r["label"]["support_type"],
                "split": r["split"],
            }
            self.pool[eid] = r["input"]["evidence_span"]
            self.paragraph_hash[eid] = r["provenance"].get("paragraph_sha256")

    def render_prompt(self, claim_id: str, k_candidates: int = 6) -> str:
        c = self.claims[claim_id]
        # show a small candidate pool (the gold span + distractors, deterministic)
        ids = sorted(self.pool)
        gold = c["gold_evidence_id"]
        cand = [gold] + [i for i in ids if i != gold][: k_candidates - 1]
        cand = sorted(set(cand))
        lines = [f"- {eid}: {self.pool[eid][:240]}" for eid in cand]
        return (
            "You verify financial claims against a fixed evidence pool.\n"
            "Cite ONE evidence_id from the pool below and judge support.\n"
            "Labels: verified_support (all elements directly entailed), "
            "partial_support (some supported, rest absent), insufficient "
            "(topical, supports nothing decisive), contradicts (any element "
            "conflicts; precedence over partial), candidate_evidence (rare).\n"
            "Never invent an evidence_id.\n\n"
            f"claim: {c['claim']}\nas_of: {c['as_of']}\n\nEVIDENCE POOL:\n"
            + "\n".join(lines)
            + '\n\nAnswer ONLY: {"cite": "<evidence_id>", "verdict": "<label>"}'
        )

    @staticmethod
    def parse(text: str) -> tuple[str | None, str | None]:
        m = re.search(r"\{[^{}]*\}", text, re.S)
        if m:
            try:
                o = json.loads(m.group(0))
                return str(o.get("cite", "")).strip() or None, str(o.get("verdict", "")).strip() or None
            except json.JSONDecodeError:
                pass
        v = re.search(r"\b(verified_support|partial_support|insufficient|contradicts|candidate_evidence)\b", text)
        return None, (v.group(1) if v else None)

    def reward(self, claim_id: str, completion: str) -> dict:
        c = self.claims[claim_id]
        cite, verdict = self.parse(completion)
        r = 0.0
        parts = {}
        if cite is None:
            parts["citation"] = 0.0
        elif cite not in self.pool:
            parts["citation"] = -1.0  # fabricated id: hard negative
        else:
            parts["citation"] = 0.3 + (0.2 if cite == c["gold_evidence_id"] else 0.0)
        parts["verdict"] = 1.0 if verdict == c["gold_label"] else 0.0
        r = parts["citation"] + parts["verdict"]
        return {"reward": round(r, 4), "parts": parts,
                "cite_ok": cite in self.pool, "cite_gold": cite == c["gold_evidence_id"],
                "verdict_ok": verdict == c["gold_label"]}


if __name__ == "__main__":
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / (
        "runs/overnight-20260629-v0.6-ai-expanded/curated/kiwi-brain-ai-expanded-v0.1/"
        "repairs/citation_contract_repair_v0.1/citation_real_eval_v1")
    env = CitationAgenticEnv(d)
    print("claims:", len(env.claims), "| pool spans:", len(env.pool))
    cid = next(iter(env.claims))
    print("gold:", env.claims[cid]["gold_evidence_id"], env.claims[cid]["gold_label"])
    good = json.dumps({"cite": env.claims[cid]["gold_evidence_id"], "verdict": env.claims[cid]["gold_label"]})
    print("perfect play reward:", env.reward(cid, good))
    print("fabricated id reward:", env.reward(cid, '{"cite":"NOPE:block:999","verdict":"insufficient"}'))
