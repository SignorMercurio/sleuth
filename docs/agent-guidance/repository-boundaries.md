# Repository Boundaries

- The installable skill package is `skills/sleuth/`: `SKILL.md`, `agents/`,
  `assets/`, and `references/`.
- Repo-level `scripts/`, `evals/`, and `reports/` are validation and evidence
  surfaces; they are not part of the installed skill package.
- `skills/sleuth/assets/report.md` is a deployed copy. Its source of truth is
  `../dossier/report.md`, synced by the dossier repo's deploy target. Do not
  hand-edit the copy; change the dossier source and re-sync with dossier's
  project-local `report-sync` skill.
- `skills/sleuth/assets/style/` is part of the tracked skill package. Add only
  sanitized samples safe for public distribution. Prefer
  `curated-ir-excerpts.md` as the Step 8 style source.
