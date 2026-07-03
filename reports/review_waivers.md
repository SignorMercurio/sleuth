# Review Waivers

Human-readable surface for `reports/review_waivers.json`. Waivers cover warning-level gates only; they record bounded, reviewer-approved risk acceptance and never convert a blocker into a pass. Expiry follows the quarterly review cadence declared in `manifest.json`.

## Active waivers

| Gate | Decision | Reviewer | Created | Expires | Reason (summary) |
| --- | --- | --- | --- | --- | --- |
| `context-budget` | accepted-risk | Mercurio | 2026-07-03 | 2026-09-22 | Initial load exceeds the governed 1300-token tier; safety contract and execution skeleton stay inline by design, references stay on-demand. Accepted 2026-06-22; step-8 dedup (2026-07-03) trimmed the overage. |
| `trust-report` | temporary-exception | Mercurio | 2026-07-03 | 2026-09-22 | Governed-release trust report deferred; maturity deliberately declared production until the evidence is generated (manifest notes, 2026-06-22). |
| `permission-runtime` | temporary-exception | Mercurio | 2026-07-03 | 2026-09-22 | Runtime permission probes deferred under the same decision; SIREN execution stays read-only per the in-skill safety contract and interface trust block. |

## Open warnings — visible, not waived

These stay warnings until fixed or explicitly accepted here:

- **`output-lab` — blind adjudication pending.** The 5 blind A/B pairs in `reports/output_blind_review_pack.md` have no recorded reviewer decisions (`reports/output_review_adjudication.json` absent). Pending pairs must not be counted as human review evidence. A decision template is staged at `reports/output_review_decisions.json`.
- **`output-lab` — assertion coverage gap (found by the model-run).** The real model-executed cross-check (below) scored baseline 80 / with-skill 80 / delta 0: the with-skill output defanged the IP but no assertion rewards that, and `use-defanged-protocol` (requires `hxxp`) is fixture-shaped for URL IoCs. Fix: add `no-raw-attacker-ip`, relax `use-defanged-protocol`, regenerate the blind pack + answer key. See `reports/output_quality_scorecard.md` → *Next Fixes*.

## Closed since last review

- **`output-lab` — model-executed run (was: none).** One case (`overview-from-findings`) now has real claude-fable-5 output for both variants: `reports/output_execution_runs.json`, snapshots under `evals/output/fixtures/overview-from-findings.*.model.md`, case def `evals/output/model_run_case.jsonl`. The honest delta is 0, which anchors the inflated static delta rather than proving skill effect — see the assertion-gap warning above.
- **`governance` — score now backed by an artifact.** `reports/governance_scorecard.json` records score 95/100 (governed band), replacing the prior manifest-notes-only claim.

## Notes

- The Review Studio decision page itself has not been generated for this package; that deferral is documented in `manifest.json` notes and is not representable as a single gate waiver.
- Raw engagement data, prompts, and outputs must never appear in waiver reasons.
