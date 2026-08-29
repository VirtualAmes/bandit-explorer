# Branching and releases — GitFlow

This repo runs **GitFlow**, the model in `~/.claude/AGENTS.md`. The one rule
that never bends: `main` is production.

Adopted from the Strato-Xen procedure (`docs/BRANCHING-AND-RELEASES.md` there),
which was written after a long-lived side branch quietly accumulated eleven
commits and a roster fix ended up one promotion from production while local
`main` sat 150 commits stale. GitFlow makes that accumulation explicit and gives
it a name: `develop`.

---

## The branches

| Branch | Lifetime | Branches from | Merges to | What it means |
|---|---|---|---|---|
| `main` | permanent | — | — | Production. Every commit is a release, tagged. |
| `develop` | permanent | `main` | — | Integration. The next release, in progress. |
| `feature/*` | short | `develop` | `develop` | One piece of work. |
| `release/*` | short | `develop` | `main` **and** `develop` | Stabilization for a named version. |
| `hotfix/*` | short | `main` (or a tag) | `main` **and** `develop` | Production is broken right now. |

**`develop` is the default branch on GitHub**, so a PR opened without an
explicit base targets it. Only a release or a hotfix may target `main`.

Deleted on merge, always (repo setting: delete branch on merge is ON). A branch
that outlives its merge is how drift starts. Do not resurrect a merged branch —
a commit pushed to one is stranded.

Merge method: **squash** for `feature/*`; **merge commit** for `release/*`,
`hotfix/*`, and back-merges (the ancestry has to stay real for the assertion
below). Rebase-merge is OFF at the repo level.

---

## Everyday work

```bash
git switch develop && git pull
git switch -c feature/short-topic
# ... work, commit ...
git push -u origin feature/short-topic
gh pr create --base develop
```

Tests green before the PR (`uv run pytest`). Merge via PR — never a local
merge to `develop`, so review and history stay on GitHub.

## Cutting a release

Versions are semver, tags are `vX.Y.Z`. Baseline for this repo:
`v0.1.0`.

```bash
git switch -c release/1.2.0 develop        # freeze: no new features after this
# bump the version in the manifest (package.json / pyproject.toml) — release branch only
git commit -am "release 1.2.0"
git push -u origin release/1.2.0
gh pr create --base main --title "Release 1.2.0"
```

Only stabilization commits go on a release branch — bug fixes, version bump,
docs. A feature that arrives mid-freeze waits for the next release.

After the PR merges to `main` (`ALLOW_PROD_MERGE=1` is the deliberate
escape hatch in the git guard — that prompt is the point):

```bash
git switch main && git pull
git tag -a v1.2.0 -m "v1.2.0 — <what shipped>"
git push origin v1.2.0
git switch -c backmerge/1.2.0 v1.2.0
git push -u origin backmerge/1.2.0
gh pr create --base develop --head backmerge/1.2.0 --title "Merge release 1.2.0 back to develop"
```

**The back-merge is the step people skip.** The version bump and any fix made
during the freeze exist only on `main` until it happens, and the next release
silently reverts them. After it merges, assert the topology:

```bash
git fetch origin
git merge-base --is-ancestor origin/main origin/develop && echo ancestry-ok
```

**Never use `main` itself as a PR head.** With delete-on-merge ON, merging a
PR whose head is `main` deletes `main` (it happened to Strato-Xen on
2026-08-29, restored from the tag). Always cut `backmerge/<ver>` from the tag.

## Hotfixes

```bash
git switch -c hotfix/1.2.1 v1.2.0     # from the TAG, not from develop
# ... smallest possible fix ...
gh pr create --base main --title "Hotfix 1.2.1"
# after merge: tag v1.2.1 on main, then backmerge/1.2.1 -> develop as above
```

Same double-merge obligation.

## Version numbers

- **patch** — hotfix, no behavior change beyond the fix
- **minor** — features
- **major** — a deliberate milestone, named in advance

The manifest version is bumped on the release branch, not on `develop`.

---

## What is enforced, and what is not

`~/.claude/hooks/git-guard.sh` (global, every session) blocks a direct commit
on `main` or `develop`, a force-push to either, deleting either from the
remote, a PR whose head is `main`/`develop`, a delegate-tier merge, a merge
into `main` without `ALLOW_PROD_MERGE=1`, and committed secrets. The repo
settings enforce delete-on-merge and no rebase-merge. Everything else here is
convention: the back-merge, the freeze rule. Those are the ones to actually
watch — `scripts/repo_census.py` reports the drift.

## Exploratory work

Exploration that may never ship is a `feature/*` branch that stays unmerged,
or an agent worktree — never a long-lived parallel trunk. If it ships, it
merges to `develop` like anything else.
