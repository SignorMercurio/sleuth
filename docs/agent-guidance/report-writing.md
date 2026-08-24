# Report Writing

- Treat findings as the report writer's fact boundary. Give the writer only the
  findings, template, curated style sample, and named writing references. Do
  not give it the investigation transcript or access to SIREN, SAS, SLS, or the
  network.
- If severity, event status, or action progress is missing, return the gap to
  the orchestrator instead of inventing it.
- Keep one authoritative home for each writing rule:
  - Template HTML comments own block-local fill rules. Edit them in dossier,
    then re-sync the deployed copy.
  - `skills/sleuth/references/report_writing_rules.md` owns cross-cutting
    constraints.
  - `skills/sleuth/references/report_style.md` owns sentence-level style.
- Elsewhere, use at most a one-line pointer to an existing rule; do not restate
  it.
