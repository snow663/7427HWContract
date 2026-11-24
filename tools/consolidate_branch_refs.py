#!/usr/bin/env python3
"""One-time GitHub branch cleanup: archive unique heads, then remove stale refs.

Default is read-only. --apply requires an exact GitHub Actions push on the
designated development branch with the ALLOW_BRANCH_PRUNE=yes gate.
All open PR heads and the main/development refs are protected.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ACTIVE = "work/pseudo-source-development"
PROTECTED = {"main", ACTIVE}
ARCHIVE_PREFIX = "archive/branches/2026-11-23/"
REPORT = Path("branch-consolidation-report.json")


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError("git " + " ".join(args) + ": " + result.stderr.strip())
    return result


def live_ref(ref):
    result = git("ls-remote", "origin", ref).stdout
    matches = [line.split("\t")[0] for line in result.splitlines()
               if line.endswith("\t" + ref)]
    if len(matches) > 1:
        raise RuntimeError("Ambiguous remote ref: " + ref)
    return matches[0] if matches else None


def open_pull_request_heads(repository):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("A GitHub token is required to protect open PR heads")
    heads = set()
    page = 1
    while page <= 20:
        url = ("https://api.github.com/repos/" + repository +
               "/pulls?state=open&per_page=100&page=" + str(page))
        request = urllib.request.Request(
            url, headers={"Authorization": "Bearer " + token,
                          "Accept": "application/vnd.github+json",
                          "X-GitHub-Api-Version": "2022-11-28"})
        with urllib.request.urlopen(request, timeout=30) as response:
            pulls = json.load(response)
        for pr in pulls:
            head = pr.get("head") or {}
            source_repo = head.get("repo") or {}
            if source_repo.get("full_name", "").lower() == repository.lower():
                heads.add(head["ref"])
        if len(pulls) < 100:
            return heads
        page += 1
    raise RuntimeError("Open PR list exceeded safe pagination limit")


def is_ancestor(older, newer):
    result = git("merge-base", "--is-ancestor", older, newer, check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError("Unable to compare commits: " + result.stderr.strip())
    return result.returncode == 0


def snapshot_heads():
    heads = {}
    for line in git("ls-remote", "--heads", "origin").stdout.splitlines():
        sha, ref = line.split("\t", 1)
        if not ref.startswith("refs/heads/"):
            raise RuntimeError("Unexpected remote ref: " + ref)
        heads[ref.removeprefix("refs/heads/")] = sha
    return heads


def archive_unique(name, sha):
    tag_ref = "refs/tags/" + ARCHIVE_PREFIX + name
    existing = live_ref(tag_ref)
    if existing and existing != sha:
        raise RuntimeError("Archive collision: " + tag_ref)
    if existing is None:
        git("push", "origin", sha + ":" + tag_ref)
    if live_ref(tag_ref) != sha:
        raise RuntimeError("Archive could not be verified: " + tag_ref)
    return tag_ref


def remove_head(name, sha):
    ref = "refs/heads/" + name
    if live_ref(ref) != sha:
        raise RuntimeError("Ref moved since snapshot: " + name)
    # The remote lease prevents racing with other writers.
    git("push", "--force-with-lease=" + ref + ":" + sha, "origin", ":" + ref)
    if live_ref(ref) is not None:
        raise RuntimeError("Branch deletion not confirmed: " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Archive unique commits and remove obsolete remote branches")
    args = parser.parse_args()
    report = {"mode": "apply" if args.apply else "dry-run",
              "protected": sorted(PROTECTED), "processed": [], "errors": []}
    try:
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        if repository != "snow663/7427HWContract":
            raise RuntimeError("Unexpected repository; refusing branch changes")
        if args.apply and not all((
            os.environ.get("ALLOW_BRANCH_PRUNE") == "yes",
            os.environ.get("GITHUB_REF_NAME") == ACTIVE,
            os.environ.get("GITHUB_EVENT_NAME") == "push")):
            raise RuntimeError("Apply mode requires the dedicated GitHub Actions push gate")
        git("fetch", "--no-tags", "origin",
            "+refs/heads/*:refs/remotes/origin/*")
        heads = snapshot_heads()
        require_heads = PROTECTED - set(heads)
        if require_heads:
            raise RuntimeError("Required branches missing: " + str(require_heads))
        active_sha = heads[ACTIVE]
        if args.apply and os.environ.get("GITHUB_SHA") != active_sha:
            raise RuntimeError("Development branch moved since workflow checkout")
        if not is_ancestor(heads["main"], active_sha):
            raise RuntimeError("Development branch no longer contains main history")
        open_prs = open_pull_request_heads(repository)
        report["open_pr_heads"] = sorted(open_prs)
        report["before_count"] = len(heads)
        report["development_head"] = active_sha
        print("Branch audit:", len(heads), "branches;", len(open_prs),
              "open PR heads; development =", active_sha, flush=True)
        for name, sha in sorted(heads.items()):
            entry = {"branch": name, "sha": sha}
            if name in PROTECTED:
                entry["result"] = "protected"
            elif name in open_prs:
                entry["result"] = "open_pr_preserved"
            else:
                ancestor = is_ancestor(sha, active_sha)
                entry["unique_commits"] = int(git(
                    "rev-list", "--count", active_sha + ".." + sha).stdout.strip())
                entry["archive_ref"] = None if ancestor else (
                    "refs/tags/" + ARCHIVE_PREFIX + name)
                entry["result"] = ("delete_merged" if ancestor else "archive_then_delete")
                print(entry["result"] + ":", name, sha, flush=True)
                if args.apply:
                    if not ancestor:
                        entry["archive_verified"] = archive_unique(name, sha)
                    remove_head(name, sha)
                    entry["result"] = "deleted"
            report["processed"].append(entry)
        report["after_count"] = len(snapshot_heads())
        print("RESULT:", report["before_count"], "->",
              report["after_count"], "branches", flush=True)
    except Exception as exc:
        report["errors"].append(str(exc))
        print("CLEANUP STOPPED:", exc, file=sys.stderr, flush=True)
        returncode = 1
    else:
        returncode = 0
    finally:
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
    return returncode


if __name__ == "__main__":
    sys.exit(main())
