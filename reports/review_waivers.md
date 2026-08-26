# Review Waivers

Human-readable surface for `reports/review_waivers.json`. Waivers cover warning-level gates only; they record bounded, reviewer-approved risk acceptance and never convert a blocker into a pass. Expiry follows the quarterly review cadence declared in `manifest.json`.

## Active waivers

None currently. All three waivers below were resolved on 2026-08-26; see "Closed since last review" for the closing evidence. Their original decision records are kept in `reports/review_waivers.json` (disclosure style — resolved waivers are marked, not deleted).

## Open warnings — visible, not waived

These stay warnings until fixed or explicitly accepted here:

- **`output-lab` — refreshed blind review pending.** The 2026-07-31 rubric and output pairs changed, so the previous five reviewer choices were cleared. `reports/output_review_decisions.json` is now a blank template and the answer key remains hidden by the adjudication output until a new blind review is recorded.
- **`output-lab` — no current paired model holdout.** Four current full reports now exercise simple, no-current-intrusion, complex, and multi-host cases, but they are skill-only forward tests. They prove contract compliance, not causal improvement against a no-skill baseline.

## Closed since last review

- **`context-budget` — resolved.** SKILL.md now loads in two phases: the resident layer (safety rails, mode routing, 8-step skeleton, report gate) is 4495 bytes (~1284 tokens), inside the governed 1300-token tier. Per-step detail moved to `references/workflow_recon.md`, `references/workflow_tracing.md`, and `references/workflow_delivery.md`, loaded on demand.
- **`trust-report` — resolved.** `scripts/gen_trust_report.py` generates the governed-release trust report (secret scan, script surface, dependency pinning, package hash) into `reports/trust_report.json` / `reports/trust_report.md`; `python3 scripts/gen_trust_report.py --check` runs in CI.
- **`permission-runtime` — resolved.** `scripts/permission_probe.py` statically verifies the interface.yaml trust block, the openai.yaml adapter's lack of extra execution capability, and SKILL.md's guardrail anchors; it runs in CI.
- **`output-lab` — complete-report regression (was: absent).** Four synthetic findings bundles and four reports generated through isolated step-8 writers now cover a simple Webshell, a historical alert with no current intrusion, a complex RCE with credential exposure, and a multi-host chain. `python3 evals/output/validate_full_reports.py` checks structure, severity, action status, IoC display, internal-language leakage, repetition, and broad case-specific length bands.
- **`output-lab` — unnatural wording follow-up (was: open).** The current style rules reject 「进程遥测」「大概率得手」 and process-meta tails, prefer customer-facing evidence terms, and forbid semicolon-compressed action chains. The refreshed micro scorecard passes all five skill-side cases; human naturalness review remains pending as recorded above.
- **`governance` — score now backed by an artifact.** `reports/governance_scorecard.json` records score 95/100 (governed band), replacing the prior manifest-notes-only claim.

## Historical reviewer feedback

The superseded 2026-07-03 blind review found correct outputs were still wordy, retained process-meta tails, and used stiff words such as 「遥测」「得手」. The 2026-07-31 style and eval changes target those findings. This note preserves provenance but is not evidence that the refreshed output pairs have passed human review.

## Notes

- The Review Studio decision page itself has not been generated for this package; that deferral is documented in `manifest.json` notes and is not representable as a single gate waiver.
- Raw engagement data, prompts, and outputs must never appear in waiver reasons.
