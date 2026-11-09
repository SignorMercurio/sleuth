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
- SIREN tool workflow or runtime compatibility: `python3 evals/runtime/run_mock_siren_tests.py`.

Combine relevant checks when surfaces overlap. Operational rules written in Markdown
are behavior changes, not prose-only exemptions. Reuse checks with unchanged inputs.

For documentation changes, also run:

```sh
bash "${HOME}/.agents/skills/health/scripts/check-doc-refs.sh" .
```

## Change-specific checks

- After changing the sections of `skills/sleuth/references/findings_spec.md`
  that the `dossier` writer reads (「文件命名」, 「内容结构」, 「结论交付层使用规则」)
  or the step-7 handoff wording, run the dossier repository's checks from
  `../dossier`: `npm run check` and `python3 evals/output/validate_full_reports.py`.
  Report fixtures and templates live there, not here.
