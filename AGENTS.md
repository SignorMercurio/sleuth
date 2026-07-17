# AGENTS.md

## Project Scope

- sleuth is a security-investigation agent skill repository. The installable
  skill package lives under `skills/sleuth/`: `SKILL.md` (SLEUTH, read-only
  remote IR investigation via SIREN, ATT&CK chain + Chinese IR report), plus
  `agents/`, `assets/`, and `references/`.
- Repo-level `scripts/`, `evals/`, and `reports/` are validation/evidence
  surfaces; they are not part of the installed skill package.
- `skills/sleuth/assets/report.md` is a deployed copy. The source of truth is
  `/Users/merc/Projects/dossier/report.md`, synced here by the dossier repo's
  deploy target. Do not hand-edit it; change the dossier source and re-sync
  (see the global `report-sync` skill).
- The skill also deploys to the remote SIREN host at
  `/root/.agents/skills/sleuth`: sync tracked files from `skills/sleuth/`
  plus the git-ignored `assets/style/` writing samples (not in `git ls-files`;
  sync them explicitly), never repo root, never `--delete`,
  `chown -R root:root` afterwards, verify remote hash.

## Operating Style

- Keep `skills/sleuth/SKILL.md` concise and imperative; preserve investigation
  behavior unless a change is explicitly requested.
- Investigation output discipline: read-only on victim hosts, conclusions split
  into confirmed vs unconfirmed, no raw sensitive payloads in reports.
- Report-writing rules keep one authoritative home per rule: template HTML
  comments own block-local fill rules (edit in dossier, then re-sync),
  `skills/sleuth/references/report_writing_rules.md` owns cross-cutting
  constraints, `skills/sleuth/references/report_style.md` owns sentence-level
  style. Echo at most a
  one-line pointer elsewhere; don't restate a rule in a second file.
- Pushes go to both GitHub (`origin`) and GitLab; check `git remote -v` before
  pushing and push both when releasing.

## Verification

- `bash /Users/merc/.agents/skills/health/scripts/check-doc-refs.sh .`
- After report-template sync:
  `cmp -s skills/sleuth/assets/report.md ../dossier/report.md`.
- After report-rule changes: generate a sample report from
  `evals/output/fixtures/web01-webshell.findings.md` per SKILL step 8 (into a
  scratch dir, not the repo) and review the prose against
  `skills/sleuth/references/report_style.md`; have the writer report rule
  conflicts it hit.
- After remote deploy: compare file hashes on the SIREN host.
