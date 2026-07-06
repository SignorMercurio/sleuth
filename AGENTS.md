# AGENTS.md

## Project Scope

- sleuth is a security-investigation agent skill repository: `SKILL.md` (SLEUTH,
  read-only remote IR investigation via SIREN, ATT&CK chain + Chinese IR report),
  plus `agents/`, `assets/`, `references/`, `scripts/`, `evals/`.
- `assets/report.md` is a deployed copy. The source of truth is
  `/Users/merc/Projects/dossier/report.md`, synced here by the dossier repo's
  deploy target. Do not hand-edit `assets/report.md`; change the dossier source
  and re-sync (see the global `report-sync` skill).
- The skill also deploys to the remote SIREN host at
  `/root/.agents/skills/sleuth`: rsync driven by `git ls-files`, never
  `--delete`, `chown -R root:root` afterwards, verify remote hash.

## Operating Style

- Keep `SKILL.md` concise and imperative; preserve investigation behavior
  unless a change is explicitly requested.
- Investigation output discipline: read-only on victim hosts, conclusions split
  into confirmed vs unconfirmed, no raw sensitive payloads in reports.
- Pushes go to both GitHub (`origin`) and GitLab; check `git remote -v` before
  pushing and push both when releasing.

## Verification

- `bash /Users/merc/.agents/skills/health/scripts/check-doc-refs.sh .`
- After report-template sync: `cmp -s assets/report.md ../dossier/report.md`.
- After remote deploy: compare file hashes on the SIREN host.
