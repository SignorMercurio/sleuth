# AGENTS.md

## Project Scope

- sleuth is a security-investigation agent skill repository. The installable
  skill package lives under `skills/sleuth/`: `SKILL.md` (SLEUTH, read-only
  remote IR investigation via SIREN, ATT&CK chain + Chinese IR report), plus
  `agents/`, `assets/`, and `references/`.
- Repo-level `scripts/`, `evals/`, and `reports/` are validation/evidence
  surfaces; they are not part of the installed skill package.
- `skills/sleuth/assets/report.md` is a deployed copy. The source of truth is
  `../dossier/report.md` in the sibling dossier repo, synced here by that repo's
  deploy target. Do not hand-edit it; change the dossier source and re-sync
  (see the global `report-sync` skill).
- `skills/sleuth/assets/style/` is part of the tracked skill package. Only add
  sanitized samples that are safe for public distribution;
  `curated-ir-excerpts.md` is the preferred Step 8 style source.
- The skill also deploys to the remote SIREN host at
  `/root/.agents/skills/sleuth`: sync tracked files from `skills/sleuth/`,
  never repo root, never `--delete`, `chown -R root:root` afterwards, and
  verify remote hashes.

## Operating Style

- Keep `skills/sleuth/SKILL.md` concise and imperative; preserve investigation
  behavior unless a change is explicitly requested.
- Investigation output discipline: read-only on victim hosts, conclusions split
  into confirmed vs unconfirmed, no raw sensitive payloads in reports.
- Alarm-driven lookup is delegated to the `sas` skill; its upstream parameter
  contract is `../log0-utils/.agents/skills/sas/SKILL.md`. Keep SLEUTH step 1.2,
  README usage, report naming, findings handoff, and selector evals synchronized
  when that contract changes; do not duplicate the CLI contract elsewhere.
- Direct `sas` remains first priority for alarms and direct `sls` for delivered
  WAF/SAS/ActionTrail logs. Alibaba Cloud control-plane, dedicated-adapter and
  cross-product gaps are delegated to the read-only `opencli-aliyun-ir` skill,
  whose source of truth lives in the `clis` repository. SLEUTH owns only scenario
  routing and the findings handoff; do not duplicate OpenCLI adapter contracts.
- Findings are the report writer's fact boundary. The writer receives only the
  findings, template, curated style sample, and named writing references; it
  must not receive the investigation transcript or access SIREN, SAS, SLS, or
  the network. Missing severity, event status, or action progress blocks the
  draft and goes back to the orchestrator instead of being invented.
- Report-writing rules keep one authoritative home per rule: template HTML
  comments own block-local fill rules (edit in dossier, then re-sync),
  `skills/sleuth/references/report_writing_rules.md` owns cross-cutting
  constraints, `skills/sleuth/references/report_style.md` owns sentence-level
  style. Echo at most a
  one-line pointer elsewhere; don't restate a rule in a second file.
- Pushes go to both GitHub (`origin`) and GitLab; check `git remote -v` before
  pushing and push both when releasing.

## Verification

- Baseline for repository changes:
  `python3 scripts/validate.py`,
  `python3 evals/output/validate_full_reports.py`, and
  `git diff --check`.
- Documentation reference audit:
  `bash "${HOME}/.agents/skills/health/scripts/check-doc-refs.sh" .`.
- After report-template sync:
  `cmp -s skills/sleuth/assets/report.md ../dossier/report.md`.
- After report-rule changes: regenerate the affected fixtures under
  `evals/output/fixtures/full_reports/` with an isolated SKILL step 8 writer,
  then run the baseline verification once and review the prose against
  `skills/sleuth/references/report_style.md`; have the writer report rule
  conflicts it hit.
- Treat complete-report fixtures as synthetic contract regression only. They do
  not replace blind human review or prove causal improvement over a no-skill
  baseline.
- After remote deploy: compare file hashes on the SIREN host.
