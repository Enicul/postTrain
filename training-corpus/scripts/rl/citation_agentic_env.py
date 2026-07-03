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

Action-space v2 (letters, D-2026-07-04-002)
-------------------------------------------
The v1 action space asks the policy to reproduce a long evidence_id verbatim,
which a 1.5B cannot do reliably, so it fabricates (F-2026-07-04-003:
fabricated_rate 0.742 post-GRPO). v2 re-renders the candidate pool as a small
LETTER menu ("A: <span>", "B: <span>", ...) and the policy answers
`{"cite": "B", "verdict": ...}`. The harness maps the chosen letter back to the
underlying evidence_id before scoring, so the model never has to copy an id.
Fabrication becomes structural: a letter is either in-menu (A..F) or off-menu,
never a hallucinated id. In v2, "fabricated" means "letter outside the rendered
menu" (still the -1.0 hard negative). The v1 raw-id space is kept intact for the
squeeze-hypothesis comparison; pick with `action_space="letters"` (or the
`--action-space letters` flag on grpo_citation.py).
"""

from __future__ import annotations

import json
import re
import string
import sys
from pathlib import Path

FIVE_WAY = {"verified_support", "partial_support", "insufficient",
            "contradicts", "candidate_evidence"}


class CitationAgenticEnv:
    def __init__(self, eval_dir: Path, action_space: str = "raw_id"):
        if action_space not in ("raw_id", "letters"):
            raise ValueError(f"action_space must be 'raw_id' or 'letters', got {action_space!r}")
        self.action_space = action_space
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

    def candidates(self, claim_id: str, k_candidates: int = 6) -> list[str]:
        """Deterministic candidate evidence_id pool for a claim (gold + distractors).

        Shared by render + reward so the letter->id mapping used to SCORE is
        exactly the one the model SAW. Independent of action_space.
        """
        c = self.claims[claim_id]
        ids = sorted(self.pool)
        gold = c["gold_evidence_id"]
        cand = [gold] + [i for i in ids if i != gold][: k_candidates - 1]
        return sorted(set(cand))

    def letter_map(self, claim_id: str, k_candidates: int = 6) -> dict[str, str]:
        """letters mode: {"A": evidence_id, "B": ...} over the candidate pool.

        Letters are assigned by the deterministic candidate order, so the same
        claim always renders the same letter->id mapping (render == score).
        """
        cand = self.candidates(claim_id, k_candidates)
        return {string.ascii_uppercase[i]: eid for i, eid in enumerate(cand)}

    def render_prompt(self, claim_id: str, k_candidates: int = 6) -> str:
        c = self.claims[claim_id]
        if self.action_space == "letters":
            lmap = self.letter_map(claim_id, k_candidates)
            lines = [f"{ltr}: {self.pool[eid][:240]}" for ltr, eid in lmap.items()]
            menu = "".join(sorted(lmap))  # e.g. "ABCDEF"
            return (
                "You verify financial claims against a fixed evidence pool.\n"
                "Pick the ONE candidate letter that best supports the claim and "
                "judge support.\n"
                "Labels: verified_support (all elements directly entailed), "
                "partial_support (some supported, rest absent), insufficient "
                "(topical, supports nothing decisive), contradicts (any element "
                "conflicts; precedence over partial), candidate_evidence (rare).\n"
                f"Cite ONE letter from {menu[0]}-{menu[-1]}; do not invent letters.\n\n"
                f"claim: {c['claim']}\nas_of: {c['as_of']}\n\nCANDIDATES:\n"
                + "\n".join(lines)
                + '\n\nAnswer ONLY: {"cite": "<letter>", "verdict": "<label>"}'
            )
        # v1 raw-id action space (kept intact for the squeeze-hypothesis comparison)
        cand = self.candidates(claim_id, k_candidates)
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
        """Parse {"cite": ..., "verdict": ...}. In letters mode `cite` is a
        single letter token (e.g. "B"); in raw_id mode it is an evidence_id.
        The verdict-only fallback is unchanged for both modes."""
        m = re.search(r"\{[^{}]*\}", text, re.S)
        if m:
            try:
                o = json.loads(m.group(0))
                return str(o.get("cite", "")).strip() or None, str(o.get("verdict", "")).strip() or None
            except json.JSONDecodeError:
                pass
        v = re.search(r"\b(verified_support|partial_support|insufficient|contradicts|candidate_evidence)\b", text)
        return None, (v.group(1) if v else None)

    def _score(self, claim_id: str, cite_ok: bool, cite_gold: bool, verdict: str | None,
               citation_part: float) -> dict:
        c = self.claims[claim_id]
        parts = {"citation": citation_part,
                 "verdict": 1.0 if verdict == c["gold_label"] else 0.0}
        return {"reward": round(parts["citation"] + parts["verdict"], 4), "parts": parts,
                "cite_ok": cite_ok, "cite_gold": cite_gold,
                "verdict_ok": verdict == c["gold_label"]}

    def reward(self, claim_id: str, completion: str, k_candidates: int = 6) -> dict:
        c = self.claims[claim_id]
        cite, verdict = self.parse(completion)
        if self.action_space == "letters":
            lmap = self.letter_map(claim_id, k_candidates)
            letter = (cite or "").strip().upper()[:1] or None
            resolved = lmap.get(letter) if letter else None
            if letter is None:
                citation_part = 0.0                       # no cite emitted
                cite_ok = cite_gold = False
            elif resolved is None:
                citation_part = -1.0                      # letter outside menu: fabricated
                cite_ok = cite_gold = False
            else:
                cite_gold = (resolved == c["gold_evidence_id"])
                citation_part = 0.3 + (0.2 if cite_gold else 0.0)
                cite_ok = True
            return self._score(claim_id, cite_ok, cite_gold, verdict, citation_part)
        # v1 raw-id action space
        if cite is None:
            citation_part = 0.0
            cite_ok = cite_gold = False
        elif cite not in self.pool:
            citation_part = -1.0  # fabricated id: hard negative
            cite_ok = cite_gold = False
        else:
            cite_gold = (cite == c["gold_evidence_id"])
            citation_part = 0.3 + (0.2 if cite_gold else 0.0)
            cite_ok = True
        return self._score(claim_id, cite_ok, cite_gold, verdict, citation_part)


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
    # v2 letters-mode smoke
    lenv = CitationAgenticEnv(d, action_space="letters")
    lmap = lenv.letter_map(cid)
    gold_letter = next((l for l, e in lmap.items() if e == lenv.claims[cid]["gold_evidence_id"]), "A")
    gl = json.dumps({"cite": gold_letter, "verdict": lenv.claims[cid]["gold_label"]})
    print("letters map:", lmap)
    print("letters perfect play reward:", lenv.reward(cid, gl))
    print("letters off-menu reward:", lenv.reward(cid, '{"cite":"Z","verdict":"insufficient"}'))
