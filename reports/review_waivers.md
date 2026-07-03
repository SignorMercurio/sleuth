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

- **`output-lab` — blind adjudication pending.** The 5 blind A/B pairs in `reports/output_blind_review_pack.md` have no recorded reviewer decisions (`reports/output_review_adjudication.json` absent). Pending pairs must not be counted as human review evidence.
- **`output-lab` — no model-executed runs.** `reports/output_quality_scorecard.md` grades static authored fixtures; the 0→100 delta is reproducibility evidence, not model-executed output evidence. At least one recorded model-executed case is needed before the delta is cited as skill effect.

## Notes

- The Review Studio decision page itself has not been generated for this package; that deferral is documented in `manifest.json` notes and is not representable as a single gate waiver.
- Raw engagement data, prompts, and outputs must never appear in waiver reasons.
