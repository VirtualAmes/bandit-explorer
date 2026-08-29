#!/usr/bin/env python3
"""Read-only repo census: branches, worktrees, primary cleanliness, GitFlow drift.

Portable version of Strato-Xen's scripts/repo-inventory.js. DELETES NOTHING.
Classifies every remote branch by GitHub PR state (never `git branch --merged`
-- squash merges make ancestry blind to merged features) and every registered
worktree by dirty state. Its output is the evidence a cleanup cites, line by
line.

Dispositions:
  removable  -- branch: newest PR merged and closed at exactly the branch tip;
                worktree: clean, not primary, branch has no open PR
  active     -- open PR, or the primary checkout
  quarantine -- dirty tree, branch with no PR record, closed-unmerged PR, or a
                merged PR whose tip moved afterwards (stranded commits)

Usage:
  python3 scripts/repo_census.py [--json] [--repo-root PATH] [--no-github]

Exit 0 always on a successful read; the report is the product. stdlib only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def sh(*args: str, cwd: str | None = None, check: bool = True) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def github_slug(root: str) -> str | None:
    try:
        url = sh("git", "-C", root, "remote", "get-url", "origin")
    except RuntimeError:
        return None
    url = url.removesuffix(".git")
    for prefix in ("git@github.com:", "https://github.com/", "ssh://git@github.com/"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return None


def pulls_by_head(slug: str) -> dict[str, list[dict]]:
    raw = sh("gh", "api", f"repos/{slug}/pulls?state=all&per_page=100", "--paginate")
    # --paginate concatenates JSON arrays; split defensively.
    pulls: list[dict] = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(raw):
        while idx < len(raw) and raw[idx].isspace():
            idx += 1
        if idx >= len(raw):
            break
        obj, end = decoder.raw_decode(raw, idx)
        pulls.extend(obj if isinstance(obj, list) else [obj])
        idx = end
    by_head: dict[str, list[dict]] = {}
    for pr in pulls:
        by_head.setdefault(pr["head"]["ref"], []).append(
            {
                "number": pr["number"],
                "state": pr["state"],
                "merged": bool(pr.get("merged_at")),
                "head_sha": pr["head"]["sha"],
                "base": pr["base"]["ref"],
            }
        )
    return by_head


def branch_rows(root: str, by_head: dict[str, list[dict]] | None) -> list[dict]:
    rows = []
    refs = sh(
        "git", "-C", root, "for-each-ref", "refs/remotes/origin",
        "--format=%(refname:short) %(objectname)",
    )
    for line in refs.splitlines():
        ref, sha = line.split(" ", 1)
        name = ref.removeprefix("origin/")
        if name in ("HEAD", "main", "develop"):
            continue
        row = {"branch": name, "sha": sha[:12], "pr": None, "class": None, "disposition": None}
        if by_head is None:
            row["class"] = "unknown (no github)"
            row["disposition"] = "quarantine"
        else:
            prs = by_head.get(name) or []
            newest = prs[0] if prs else None
            if not newest:
                row["class"], row["disposition"] = "no-pr", "quarantine"
            elif newest["state"] == "open":
                row["class"], row["disposition"] = "open-pr", "active"
            elif newest["merged"]:
                if newest["head_sha"] == sha:
                    row["class"], row["disposition"] = "merged-pr", "removable"
                else:
                    row["class"], row["disposition"] = "merged-pr-stranded-tip", "quarantine"
            else:
                row["class"], row["disposition"] = "closed-unmerged-pr", "quarantine"
            if newest:
                row["pr"] = f"#{newest['number']}->{newest['base']}"
        rows.append(row)
    return rows


def local_gone_branches(root: str) -> list[str]:
    out = sh("git", "-C", root, "for-each-ref", "refs/heads",
             "--format=%(refname:short) %(upstream:track)")
    return [l.split(" ", 1)[0] for l in out.splitlines() if "[gone]" in l]


def worktree_rows(root: str, primary: str, by_head: dict[str, list[dict]] | None) -> list[dict]:
    rows = []
    porcelain = sh("git", "-C", root, "worktree", "list", "--porcelain")
    current: dict = {}
    for line in porcelain.splitlines() + [""]:
        if not line:
            if current:
                rows.append(current)
            current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current = {"path": value, "branch": None, "detached": False}
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "detached":
            current["detached"] = True
    for row in rows:
        path = row["path"]
        exists = Path(path).exists()
        row["exists"] = exists
        row["dirty"] = None
        if exists:
            status = sh("git", "-C", path, "status", "--porcelain", check=False)
            row["dirty"] = len([l for l in status.splitlines() if l.strip()])
        is_primary = Path(path).resolve() == Path(primary).resolve()
        row["class"] = "primary" if is_primary else "ephemeral"
        if is_primary:
            row["disposition"] = "active"
        elif not exists:
            row["disposition"] = "prunable (path missing)"
        elif row["dirty"]:
            row["disposition"] = "quarantine (dirty)"
        elif by_head is not None and row["branch"] and any(
            p["state"] == "open" for p in by_head.get(row["branch"], [])
        ):
            row["disposition"] = "active (open PR)"
        else:
            row["disposition"] = "removable"
    return rows


def gitflow_drift(root: str) -> list[str]:
    drift = []
    branches = sh("git", "-C", root, "for-each-ref", "refs/remotes/origin", "--format=%(refname:short)")
    names = {b.removeprefix("origin/") for b in branches.splitlines()}
    if "develop" not in names:
        drift.append("no origin/develop branch — GitFlow not enabled")
    if "main" not in names:
        drift.append("no origin/main branch")
    if "main" in names and "develop" in names:
        anc = subprocess.run(
            ["git", "-C", root, "merge-base", "--is-ancestor", "origin/main", "origin/develop"]
        ).returncode
        if anc != 0:
            drift.append("origin/main is NOT an ancestor of origin/develop — back-merge missing")
    head = sh("git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD", check=False)
    if head not in ("develop", "main"):
        drift.append(f"primary checkout is on '{head}', not develop")
    if head == "develop" and "develop" in names:
        behind = sh("git", "-C", root, "rev-list", "--count", "develop..origin/develop", check=False)
        if behind and behind != "0":
            drift.append(f"local develop is {behind} commit(s) behind origin/develop")
    status = sh("git", "-C", root, "status", "--porcelain", check=False)
    n = len([l for l in status.splitlines() if l.strip()])
    if n:
        drift.append(f"primary checkout has {n} uncommitted/untracked entries")
    tags = sh("git", "-C", root, "tag", check=False)
    if not tags:
        drift.append("no release tags — main has no tagged baseline")
    return drift


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-github", action="store_true", help="skip gh api (offline); every branch quarantines")
    args = ap.parse_args()

    root = args.repo_root or sh("git", "rev-parse", "--show-toplevel")
    primary = sh("git", "-C", root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    primary = str(Path(primary).parent)
    sh("git", "-C", root, "fetch", "--prune", "--quiet", check=False)

    slug = None if args.no_github else github_slug(root)
    by_head = None
    if slug:
        try:
            by_head = pulls_by_head(slug)
        except RuntimeError as exc:
            print(f"warning: github read failed ({exc}); branches quarantine", file=sys.stderr)

    report = {
        "repo": slug or root,
        "primary": primary,
        "gitflow_drift": gitflow_drift(primary),
        "branches": branch_rows(root, by_head),
        "local_gone_branches": local_gone_branches(root),
        "worktrees": worktree_rows(root, primary, by_head),
    }
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"# Repo census — {report['repo']}")
    print("\n## GitFlow drift")
    for d in report["gitflow_drift"] or ["none"]:
        print(f"- {d}")
    counts: dict[str, int] = {}
    for row in report["branches"]:
        counts[row["disposition"]] = counts.get(row["disposition"], 0) + 1
    print(f"\n## Remote branches ({len(report['branches'])}): " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for row in sorted(report["branches"], key=lambda r: (r["disposition"], r["branch"])):
        print(f"- {row['disposition']:10} {row['branch']}  [{row['class']}{' ' + row['pr'] if row['pr'] else ''}]")
    print(f"\n## Local branches with gone upstream ({len(report['local_gone_branches'])})")
    for b in report["local_gone_branches"]:
        print(f"- {b}")
    print(f"\n## Worktrees ({len(report['worktrees'])})")
    for row in report["worktrees"]:
        print(f"- {row['disposition']:22} {row['path']}  [{row['branch'] or 'detached'}; dirty={row['dirty']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
