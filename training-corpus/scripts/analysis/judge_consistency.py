#!/usr/bin/env python3
"""Judge / auditor consistency analysis over the frozen citation and risk evals.

Reads only the frozen audit vote files (read-only) and writes summaries into
training-corpus/scripts/analysis/out/. It NEVER writes into the frozen eval
dirs.

For each dataset it computes, from the two independent blind annotation passes
(pass A / pass B):

  - overall pass-A/pass-B agreement rate (exact-label match)
  - per-label agreement (a 2-pass confusion matrix)
  - the list of disagreement rows (sample_id + both votes)
  - for citation, agreement conditional on the pass-A label class

Datasets:
  citation : votes_passA.jsonl (131) vs votes_passB.jsonl (130); label is the
             five-way support class.
  risk     : the double annotation is split across three shuffled batches
             rb1/rb2/rb3 (A vs B each). The compound label is
             (risk_level, requires_human_gate). The 47 golden syn rows that the
             normalizer first rendered empty (F-2026-07-02-004) were re-audited
             in rsyn_A/rsyn_B; we report the empty-render batch and the clean
             re-audit separately so the render-bug signal stays visible.

stdlib only.
"""
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

BASE = os.path.join(
    REPO,
    "training-corpus/runs/overnight-20260629-v0.6-ai-expanded/curated",
    "kiwi-brain-ai-expanded-v0.1/repairs",
)
CIT = os.path.join(BASE, "citation_contract_repair_v0.1/citation_real_eval_v1")
RISK = os.path.join(BASE, "risk_contract_repair_v0.1b/risk_real_eval_v1")

EMPTY_MARK = "INVALID_EMPTY_RENDER"


def read_jsonl(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def index_by(rows, key="sample_id"):
    out = {}
    for r in rows:
        out[r[key]] = r
    return out


def agreement(pairs):
    """pairs: list of (sample_id, label_a, label_b). Returns stats dict."""
    both = [(sid, a, b) for sid, a, b in pairs if a is not None and b is not None]
    agree = [t for t in both if t[1] == t[2]]
    disagree = [t for t in both if t[1] != t[2]]
    # 2-pass confusion: count of (label_a, label_b)
    confusion = Counter((a, b) for _, a, b in both)
    return both, agree, disagree, confusion


def per_label_breakdown(both):
    """Agreement conditional on the pass-A label class."""
    by = defaultdict(lambda: {"n": 0, "agree": 0})
    for _sid, a, b in both:
        by[a]["n"] += 1
        if a == b:
            by[a]["agree"] += 1
    out = {}
    for label, d in by.items():
        out[label] = {
            "n": d["n"],
            "agree": d["agree"],
            "agreement_rate": round(d["agree"] / d["n"], 4) if d["n"] else None,
        }
    return out


def confusion_to_jsonable(confusion):
    return [
        {"pass_a": a, "pass_b": b, "count": c}
        for (a, b), c in sorted(confusion.items(), key=lambda kv: -kv[1])
    ]


# ---------------------------------------------------------------- citation ---
def analyze_citation():
    a = index_by(read_jsonl(os.path.join(CIT, "audit/votes_passA.jsonl")))
    b = index_by(read_jsonl(os.path.join(CIT, "audit/votes_passB.jsonl")))
    all_ids = sorted(set(a) | set(b))
    pairs = []
    missing = []
    for sid in all_ids:
        la = a[sid]["label"] if sid in a else None
        lb = b[sid]["label"] if sid in b else None
        if la is None or lb is None:
            missing.append({"sample_id": sid, "pass_a": la, "pass_b": lb})
        pairs.append((sid, la, lb))

    both, agree, disagree, confusion = agreement(pairs)
    disagree_rows = []
    for sid, la, lb in disagree:
        disagree_rows.append(
            {
                "sample_id": sid,
                "pass_a": la,
                "pass_b": lb,
                "pass_a_note": a.get(sid, {}).get("note"),
                "pass_b_note": b.get(sid, {}).get("note"),
            }
        )

    return {
        "dataset": "citation_real_eval_v1",
        "label_space": ["verified_support", "partial_support", "insufficient", "contradicts"],
        "n_pass_a": len(a),
        "n_pass_b": len(b),
        "n_both_annotated": len(both),
        "n_missing_one_pass": len(missing),
        "missing_rows": missing,
        "agree": len(agree),
        "disagree": len(disagree),
        "agreement_rate": round(len(agree) / len(both), 4) if both else None,
        "agreement_conditional_on_pass_a_label": per_label_breakdown(both),
        "two_pass_confusion": confusion_to_jsonable(confusion),
        "disagreement_rows": disagree_rows,
    }


# -------------------------------------------------------------------- risk ---
def _risk_label(v):
    """Compound label as a string; None if the row was an empty render."""
    if v is None:
        return None, False
    note = v.get("note") or ""
    is_empty = EMPTY_MARK in note
    lvl = v.get("risk_level")
    gate = v.get("requires_human_gate")
    return f"{lvl}/gate={str(gate).lower()}", is_empty


def _risk_pass(files_a, files_b):
    a, b = {}, {}
    for f in files_a:
        a.update(index_by(read_jsonl(f)))
    for f in files_b:
        b.update(index_by(read_jsonl(f)))
    all_ids = sorted(set(a) | set(b))
    pairs, empties = [], []
    for sid in all_ids:
        la, ea = _risk_label(a.get(sid))
        lb, eb = _risk_label(b.get(sid))
        if ea or eb:
            empties.append({"sample_id": sid, "pass_a_empty": ea, "pass_b_empty": eb})
        pairs.append((sid, la, lb))
    return a, b, pairs, empties


def analyze_risk_block(name, files_a, files_b, exclude_empty):
    a, b, pairs, empties = _risk_pass(files_a, files_b)
    if exclude_empty:
        empty_ids = {e["sample_id"] for e in empties}
        pairs = [p for p in pairs if p[0] not in empty_ids]
    both, agree, disagree, confusion = agreement(pairs)
    disagree_rows = []
    for sid, la, lb in disagree:
        disagree_rows.append(
            {
                "sample_id": sid,
                "pass_a": la,
                "pass_b": lb,
                "pass_a_note": a.get(sid, {}).get("note"),
                "pass_b_note": b.get(sid, {}).get("note"),
            }
        )
    return {
        "block": name,
        "n_both_annotated": len(both),
        "n_empty_render_rows": len(empties),
        "empty_render_rows": empties,
        "agree": len(agree),
        "disagree": len(disagree),
        "agreement_rate": round(len(agree) / len(both), 4) if both else None,
        "agreement_conditional_on_pass_a_label": per_label_breakdown(both),
        "two_pass_confusion": confusion_to_jsonable(confusion),
        "disagreement_rows": disagree_rows,
    }


def analyze_risk():
    ad = os.path.join(RISK, "audit")
    p = lambda n: os.path.join(ad, n)
    # primary double annotation, the three shuffled batches, empty renders excluded
    primary = analyze_risk_block(
        "primary_rb1_rb2_rb3_clean",
        [p("rb1_A.jsonl"), p("rb2_A.jsonl"), p("rb3_A.jsonl")],
        [p("rb1_B.jsonl"), p("rb2_B.jsonl"), p("rb3_B.jsonl")],
        exclude_empty=True,
    )
    # same batches WITHOUT excluding empties, to surface the render-bug signal
    raw = analyze_risk_block(
        "primary_rb1_rb2_rb3_including_empty_render",
        [p("rb1_A.jsonl"), p("rb2_A.jsonl"), p("rb3_A.jsonl")],
        [p("rb1_B.jsonl"), p("rb2_B.jsonl"), p("rb3_B.jsonl")],
        exclude_empty=False,
    )
    # clean re-audit of the 47 syn rows after the normalizer fix
    resyn = analyze_risk_block(
        "syn_reaudit_after_render_fix_rsyn",
        [p("rsyn_A.jsonl")],
        [p("rsyn_B.jsonl")],
        exclude_empty=True,
    )
    return {
        "dataset": "risk_real_eval_v1",
        "label_space": "risk_level in {high,medium,low} x requires_human_gate in {true,false}",
        "note": (
            "Primary double annotation is the rb1/rb2/rb3 shuffled batches. The "
            "47 golden syn rows first rendered empty by a normalizer family-dispatch "
            "bug (F-2026-07-02-004); the clean re-audit is rsyn. The "
            "_including_empty_render block quantifies how many rows the render bug "
            "cost, which both blind passes flagged identically."
        ),
        "blocks": {
            "primary_clean": primary,
            "primary_including_empty_render": raw,
            "syn_reaudit_after_render_fix": resyn,
        },
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    cit = analyze_citation()
    risk = analyze_risk()

    with open(os.path.join(OUT, "judge_consistency_citation.json"), "w") as fh:
        json.dump(cit, fh, indent=2)
    with open(os.path.join(OUT, "judge_consistency_risk.json"), "w") as fh:
        json.dump(risk, fh, indent=2)

    summary = {
        "generated_by": "training-corpus/scripts/analysis/judge_consistency.py",
        "inputs_are_frozen_readonly": True,
        "citation": {
            "n_both_annotated": cit["n_both_annotated"],
            "agreement_rate": cit["agreement_rate"],
            "disagree": cit["disagree"],
            "n_missing_one_pass": cit["n_missing_one_pass"],
            "agreement_conditional_on_pass_a_label": {
                k: v["agreement_rate"]
                for k, v in cit["agreement_conditional_on_pass_a_label"].items()
            },
        },
        "risk": {
            "primary_clean": {
                "n_both_annotated": risk["blocks"]["primary_clean"]["n_both_annotated"],
                "agreement_rate": risk["blocks"]["primary_clean"]["agreement_rate"],
                "disagree": risk["blocks"]["primary_clean"]["disagree"],
            },
            "syn_reaudit_after_render_fix": {
                "n_both_annotated": risk["blocks"]["syn_reaudit_after_render_fix"]["n_both_annotated"],
                "agreement_rate": risk["blocks"]["syn_reaudit_after_render_fix"]["agreement_rate"],
                "disagree": risk["blocks"]["syn_reaudit_after_render_fix"]["disagree"],
            },
            "render_bug_rows_flagged_by_both_passes": risk["blocks"][
                "primary_including_empty_render"
            ]["n_empty_render_rows"],
        },
    }
    with open(os.path.join(OUT, "judge_consistency_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
