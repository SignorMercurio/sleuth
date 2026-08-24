# Release Operations

## Remote deployment

- Deploy the skill to `/root/.agents/skills/sleuth` only when explicitly
  requested.
- Sync tracked files from `skills/sleuth/`, never from the repository root and
  never with `--delete`.
- After syncing, run `chown -R root:root` on the deployed skill and compare
  local and remote file hashes.

## Git remotes

- When an explicitly authorized release includes pushing, inspect
  `git remote -v` and push to both GitHub (`origin`) and GitLab.
