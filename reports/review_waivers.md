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

- **`output-lab` — main rubric not yet synced (low priority, intentional).** The defang-aware `no-raw-attacker-ip` assertion is only on the separate model-run case, not the main `cases.jsonl`/blind pack. Porting it invalidates the closed adjudication (rubric change → blind-pack sha change → re-attest), so it's deferred to the next blind review round. See `reports/output_quality_scorecard.md` → *Next Fixes*.

## Closed since last review

- **`output-lab` — assertion coverage gap (was: open).** The model-run rubric now rewards the real skill increment: dropped the URL-shaped `use-defanged-protocol` (N/A to an IP IoC), added `no-raw-attacker-ip`. Re-run scores baseline 80 / with-skill 100 / delta +20 — the first delta reflecting skill effect, not a straw-man gap. Done on the separate case `overview-from-findings-modelrun` so the closed adjudication stays valid.
- **`output-lab` — blind adjudication (was: pending).** All 5 blind A/B pairs adjudicated 2026-07-03, reviewer `mercury`, 5/5 agreement with the answer key, `ready_for_human_evidence: true`. Decisions in `reports/output_review_decisions.json`, adjudication in `reports/output_review_adjudication.json`. Note: these are static-fixture pairs, so 5/5 confirms the harness, not real-holdout skill strength. Reviewer flagged a recurring quality issue — see the style follow-up below.
- **`output-lab` — model-executed run (was: none).** One case (`overview-from-findings`) now has real claude-fable-5 output for both variants: `reports/output_execution_runs.json`, snapshots under `evals/output/fixtures/overview-from-findings.*.model.md`, case def `evals/output/model_run_case.jsonl`. The honest delta is 0, which anchors the inflated static delta rather than proving skill effect — see the assertion-gap warning above.
- **`governance` — score now backed by an artifact.** `reports/governance_scorecard.json` records score 95/100 (governed band), replacing the prior manifest-notes-only claim.

## Reviewer-flagged follow-up (from blind adjudication)

The blind review recorded a consistent qualitative note across 3 of 5 cases: the winning (skill) outputs are correct but wordy, trailing self-explanatory process/meta clauses (「按推测记录并交叉其他证据」, 「按证据驱动原则不点亮该技术，仅在证据缺口里说明」) and stiff word choices (「遥测」「得手」). Captured as a new rule in `references/report_style.md` (反 AI 腔清单): give the judgment and its evidence, then stop — drop the trailing "按 X 原则做 Y" tails.

## Notes

- The Review Studio decision page itself has not been generated for this package; that deferral is documented in `manifest.json` notes and is not representable as a single gate waiver.
- Raw engagement data, prompts, and outputs must never appear in waiver reasons.
