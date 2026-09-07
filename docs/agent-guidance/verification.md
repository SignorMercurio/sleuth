# Verification

## Baseline

Run `git diff --check` for every change. For release readiness or cross-cutting
changes to the installable Skill contract, run all checks below. For narrower
changes, select the applicable checks:

- Ordinary repository prose or instruction routing: check affected references.
- Skill metadata, structure, references or routing/workflow semantics:
  `python3 scripts/validate.py`.
- Permission, trust or allowed-command contracts: `python3 scripts/permission_probe.py`.
- Trust-report inputs (tracked files, scripts, dependencies or the Skill package):
  `python3 scripts/gen_trust_report.py --check`; regenerate evidence as described in
  [Runtime governance](runtime-governance.md).
- Report contracts: `python3 evals/output/validate_full_reports.py`.
- SIREN tool workflow or runtime compatibility: `python3 evals/runtime/run_mock_siren_tests.py`.

Combine relevant checks when surfaces overlap. Operational rules written in Markdown
are behavior changes, not prose-only exemptions. Reuse checks with unchanged inputs.

For documentation changes, also run:

```sh
bash "${HOME}/.agents/skills/health/scripts/check-doc-refs.sh" .
```

## Change-specific checks

- After syncing the report template, run
  `cmp -s skills/sleuth/assets/report.md ../dossier/report.md`.
- After changing report rules, regenerate the affected fixtures under
  `evals/output/fixtures/full_reports/` with an isolated SKILL Step 8 writer.
  Then run the applicable checks above, review the prose against
  `skills/sleuth/references/report_style.md`, and have the writer report any rule
  conflicts.
- Treat complete-report fixtures as synthetic contract regression only. They do
  not replace blind human review or prove causal improvement over a no-skill
  baseline.
