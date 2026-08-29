# Operations hygiene — the standing rules

The portable core of the Strato-Xen operating procedure
(`docs/OPERATIONS-HYGIENE.md` and `docs/REPO-LIFECYCLE-CONTRACT.md` there),
ratified by Brian 2026-08-21: one bounded task at a time, isolated worktrees,
durable state plus git history as the memory, a clean environment at the end
of every session, and end-to-end verification before anything is called done.

This document is current law for this repo, kept short deliberately. Where
`AGENTS.md` is silent, this applies; where this is silent, `~/.claude/AGENTS.md`
applies.

## The one-sentence version

Every object you create — branch, worktree, file, process — has an owner, a
purpose, a lifecycle state, and a planned death; if you cannot name all four,
do not create it.

## Worktrees

Classes:

1. **Primary** (Brian's checkout under `~/Dev/Projects/`) — the control root.
   NEVER a development workspace for an agent. No agent commits, edits, or
   installs dependencies here. Every git command anywhere is `git -C <absolute>`.
2. **Production** (only if this repo has a deploy target; named in `AGENTS.md`)
   — detached at the exact release tag. Deploy target, not a sandbox.
3. **Ephemeral task/review trees** — created per task from fresh
   `origin/develop`, under `.claude/worktrees/<topic>` (gitignored), one bounded
   task per tree, REMOVED BY THEIR CREATOR when the PR merges. A merged PR with a
   live worktree is a hygiene bug.

Rules that bind all classes:

- One bounded task per tree. Never stack a second PR on an unmerged branch —
  with delete-on-merge ON, GitHub closes the stacked PR when its base vanishes.
- Verification trees are DATALESS: a real dependency install, no symlinks into
  private data. A symlink is not a read-only control.
- Dirty or unclassified trees QUARANTINE — they are never auto-removed; they get
  a disposition line on an issue.
- Two concurrent sessions never share a mutable checkout.

## Branches

- `feature/*` from `origin/develop`, one topic, back via PR, **squash merge**.
- `release/*`, `hotfix/*`, `backmerge/*`: **merge commit**, then assert
  `git merge-base --is-ancestor origin/main origin/develop`.
- Delete-on-merge is ON at the repo level; rebase-merge is OFF.
- Cleanup uses GitHub PR state, never `git branch --merged` (squash blinds
  ancestry). `removable` means a MERGED PR closed at exactly the branch tip;
  everything else quarantines with a named reason. `scripts/repo_census.py`
  is the read-only census that produces that list.

## Sessions and evidence

- **Reconstruct from durable state**, not conversational memory: issues, PR
  comments, and git history are the record. If it is not on an issue or in a
  commit, it did not happen.
- **One bounded increment, verified end to end, then a clean state.** Ending a
  session with uncommitted work, an unposted result, or an unremoved ephemeral
  tree is ending it mid-task.
- **Verify, don't assert**: before claiming done/works/fixed, run the check and
  show the command + output.
- **Compressed findings, not transcripts**: reports are the conclusion plus
  pointers to evidence.

## Communication and state

- GitHub issues/PRs are the ONLY control plane. A dispatch that exists only in
  a pane or a chat does not exist.
- Every ticket carries an explicit "Done means:" naming a checkable outcome.
- Completion is a reviewed PR against `develop`. A delegate never merges its own
  work; opening the PR is the handoff.

## Scratch paths

Temporary output belongs under the session scratchpad or an OS temp root, never
under the repo root. Adding a root `tmp/` to `.gitignore` is not a fix — it
hides the violation.

## Cadence

- **Per task**: creator removes their ephemeral tree on merge.
- **Per session end**: `scripts/repo_census.py` reads clean (no stranded
  commits, no PR-less pushed branches, no removable trees).
- **Weekly**: census sweep; removable branches/trees deleted with the log
  posted to an issue; quarantine dispositions ruled one by one.

## Enforcement

Mechanical where possible (repo settings, the global git guard, CI on every
PR, the census), review otherwise. A rule that exists only as a reminder is a
bug to convert into a control.
