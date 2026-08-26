# Verification

## Baseline

Run for every repository change:

```sh
python3 scripts/validate.py
python3 scripts/permission_probe.py
python3 scripts/gen_trust_report.py --check
python3 evals/output/validate_full_reports.py
python3 evals/runtime/run_mock_siren_tests.py
git diff --check
```

For documentation changes, also run:

```sh
bash /Users/merc/.agents/skills/health/scripts/check-doc-refs.sh .
```

## Change-specific checks

- After syncing the report template, run
  `cmp -s skills/sleuth/assets/report.md ../dossier/report.md`.
- After changing report rules, regenerate the affected fixtures under
  `evals/output/fixtures/full_reports/` with an isolated SKILL Step 8 writer.
  Then run the baseline once, review the prose against
  `skills/sleuth/references/report_style.md`, and have the writer report any
  rule conflicts.
- Treat complete-report fixtures as synthetic contract regression only. They do
  not replace blind human review or prove causal improvement over a no-skill
  baseline.
