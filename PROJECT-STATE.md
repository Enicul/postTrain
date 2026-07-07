# PROJECT-STATE — postTrain
_Updated: 2026-07-07, branch main (synced with origin, HEAD 078d8a1)_

## Last session did
- Full GPU campaign COMPLETE: A1→A3, multi-seed, full-FT probes, env v0.3 declared
  SATURATED (7 configs hit oracle 0.8473); five self-corrections all archived.
- Citation chain CLOSED (action-space fix 87%→0 fabrication; class-balance 6x verdict;
  capacity & RL increment both null — data is the sole lever).
- env v0.4 memory exam built (592 seeds / 232 twin pairs / frozen test 121) + eval
  harness (eval_v04.py). Three-arm first exam INTERRUPTED (owner's other GPU job).
- Interview-readiness pack shipped: RESUME_DRAFT_zh_en, 90s README, PITCH_3MIN_zh,
  INTERVIEW_AGENT_HANDBOOK, WHITEBOARD_FUNDAMENTALS + storyline/report/handbook artifacts.

## Stopped at
- Owner leaving to prepare for interviews using the shipped materials.

## Running / scheduled
- Nothing. GPU 0 free (owner's own deepseek/confiqa job finished). No crons, no watchers.

## Awaiting user (decide next session)
- Run the v0.4 three-arm first exam when GPU is free? (commands ready in rl/README)
- Citation collection batch-2 (277→400+ rows)?
- Plan C (training-free GRPO) real run — still queued, never executed.

## Next steps
1. v0.4 three-arm exam (none/digest/raw, 1.5B prompted) — 15 min GPU.
2. Interview drills: new session reads docs/INTERVIEW_AGENT_HANDBOOK.md as interviewer.
3. Real-run anchoring of 30-50 seeds (the sim≠real answer's missing half).

## Don't forget / traps
- GPU box scripts synced to commit e571324+ via rsync (box repo is NOT a git remote).
- rsync from box regresses run_manifest redactions — always `git checkout -- <manifests>` after.
- One-committer-per-repo rule; kill-by-PID not pkill-pattern on the shared box.
- Interview assets: storyline artifact (7 acts) + campaign report + zen handbook are on claude.ai artifacts.
