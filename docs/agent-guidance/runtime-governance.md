# Runtime Governance

- Treat `evals/runtime/` as deterministic regression for the mock SIREN engine,
  scenario data, fault handling, and transcript checker. Passing it does not
  prove that an agent reaches the correct conclusion; use the model drill and semantic review in
  `evals/runtime/README.md` for model-behavior review.
- `evals/runtime/run_agent_drill.py` is an opt-in exception to offline checks:
  it invokes the user's configured Claude Code model service and writes a new,
  explicitly selected directory outside the repository. It exposes only mock
  SIREN and scoped local file tools to the model, plus the Task sub-agent tool
  under the same grants unless `--no-subagents` is passed; it is not run by CI or shipped
  in the Skill. After editing it, review those capabilities; do not describe the
  runner as offline.
- `evals/runtime/mock_siren/policy.py` and the mock server tool definitions are
  snapshots of the real SIREN contract. When that contract changes, compare the
  upstream behavior and update the snapshot and its tests together.
- `evals/semantic_config.json` `guardrail_contract.required_anchors` owns the
  guardrail anchors that `scripts/validate.py` checks in `SKILL.md`; the same
  script checks the trust block of `agents/interface.yaml` and
  `agents/openai.yaml`. Preserve the safety behavior and update the anchors with
  any intentional wording change.
- `scripts/validate.py` scans git-tracked files for credentials. Do not add an
  exclusion to pass it; replace the value with a placeholder.
- Keep repository-check dependencies exactly pinned in `requirements.txt` and
  install them with `python3 -m pip install -r requirements.txt`.
