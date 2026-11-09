# Repository Boundaries

- The installable skill package is `skills/sleuth/`: `SKILL.md`, `agents/`, and
  `references/`. It carries no report template, style sample, or writing rule.
- Report generation, merging, revision, and review belong to the `dossier`
  skill in the sibling repository (`../dossier/skills/dossier/`), which also
  owns the report templates. Install both skills in the same skills directory:
  `dossier` reads `../sleuth/references/findings_spec.md` across packages at
  write time; sleuth never reads `dossier`.
- `skills/sleuth/references/findings_spec.md` is therefore a cross-repository
  contract. Its 「文件命名」, 「内容结构」, and 「结论交付层使用规则」 sections
  are what the `dossier` writer relies on; after changing them, run the dossier
  repository's checks (see the verification guide).
- Repo-level `scripts/`, `evals/`, and `reports/` are validation and evidence
  surfaces; they are not part of the installed skill package.
