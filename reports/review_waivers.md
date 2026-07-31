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

- **`output-lab` — refreshed blind review pending.** The 2026-07-31 rubric and output pairs changed, so the previous five reviewer choices were cleared. `reports/output_review_decisions.json` is now a blank template and the answer key remains hidden by the adjudication output until a new blind review is recorded.
- **`output-lab` — no current paired model holdout.** Four current full reports now exercise simple, no-current-intrusion, complex, and multi-host cases, but they are skill-only forward tests. They prove contract compliance, not causal improvement against a no-skill baseline.

## Closed since last review

- **`output-lab` — complete-report regression (was: absent).** Four synthetic findings bundles and four reports generated through isolated step-8 writers now cover a simple Webshell, a historical alert with no current intrusion, a complex RCE with credential exposure, and a multi-host chain. `python3 evals/output/validate_full_reports.py` checks structure, severity, action status, IoC display, internal-language leakage, repetition, and broad case-specific length bands.
- **`output-lab` — unnatural wording follow-up (was: open).** The current style rules reject 「进程遥测」「大概率得手」 and process-meta tails, prefer customer-facing evidence terms, and forbid semicolon-compressed action chains. The refreshed micro scorecard passes all five skill-side cases; human naturalness review remains pending as recorded above.
- **`governance` — score now backed by an artifact.** `reports/governance_scorecard.json` records score 95/100 (governed band), replacing the prior manifest-notes-only claim.

## Historical reviewer feedback

The superseded 2026-07-03 blind review found correct outputs were still wordy, retained process-meta tails, and used stiff words such as 「遥测」「得手」. The 2026-07-31 style and eval changes target those findings. This note preserves provenance but is not evidence that the refreshed output pairs have passed human review.

## Notes

- The Review Studio decision page itself has not been generated for this package; that deferral is documented in `manifest.json` notes and is not representable as a single gate waiver.
- Raw engagement data, prompts, and outputs must never appear in waiver reasons.
