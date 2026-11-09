# Release Operations

## Remote deployment

- Deploy the skill only when explicitly requested, to the shared copy
  `/opt/raven-skills/sleuth`. Raven loads it from there, and
  `/root/.agents/skills/sleuth` is a symlink to it for host agents. Update the
  contents in place; never replace the symlink with a directory.
- Do not manage the deployed skill with `npx skills add` or `npx skills update`
  on SIREN; the CLI reinstalls a real directory over the symlink.
- Sync tracked files from `skills/sleuth/`, never from the repository root and
  never with `--delete`.
- After syncing, run `chown -R root:root` on the deployed skill, keep
  directories `0755` and files `0644`, and compare local and remote file hashes.
- The `dossier` skill is deployed beside it the same way, from the dossier
  repository's `skills/dossier/` to `/opt/raven-skills/dossier` with the
  `/root/.agents/skills/dossier` symlink. Deploy both when a change to the
  findings contract spans the two skills.

## Git remotes

- When an explicitly authorized release includes pushing, inspect
  `git remote -v` and push to both GitHub (`origin`) and GitLab.
