# Verification

## Baseline

Run `git diff --check` for every change. For release readiness or cross-cutting
changes to the installable Skill contract, run all checks below. For narrower
changes, select the applicable checks:

- Ordinary repository prose or instruction routing: check affected references.
- Skill metadata, structure, references, routing/workflow semantics, guardrail
  anchors, the interface trust block, or any new tracked file (secret scan):
  `python3 scripts/validate.py`.
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
