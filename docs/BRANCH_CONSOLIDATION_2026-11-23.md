# Branch consolidation — 2026-11-23

**Branch policy:** `main` is the validated release baseline.
`work/pseudo-source-development` is the **only cumulative active development
branch**. All incremental source work, experiments destined for the same OS,
tests and documentation go on that branch. Do not create a new routine-by-routine
development branch. Open a short-lived PR branch only when an independently
reviewable change genuinely requires one; remove it after merging.

## One-time cleanup with full commit preservation

The dedicated `branch-consolidation.yml` push workflow runs only when a
commit on the active development branch carries
`[prune-stale-branches]`. The default script is read-only. Its privileged
apply mode requires the exact repository, Actions push/ref gate and explicit
environment authorization.

The script enumerates **all** heads from Git, checks the open-PR list using
the GitHub API, and refuses to modify `main`,
`work/pseudo-source-development`, or an **open PR head**. It verifies that
the development head contains the latest mainline history.

For other branches:

- If the head is already an ancestor of the active branch, the branch pointer
  is redundant and may be deleted; the commit remains reachable from the
  development branch.
- If it has unique commits, the script **first creates and verifies** a
  lightweight tag at the exact original head named
  `archive/branches/2026-11-23/<original-branch-name>`. Only then may
  the branch pointer be deleted. These tags are not merged into active
  development automatically.
- Before each removal, an exact-SHA remote lease prevents deleting a
  branch that another writer has advanced. A moved ref, authentication
  failure, unverified archive, pagination failure or uncertain merge base
  stops cleanup.
- A GitHub Actions artifact captures the branch-level decisions. Open PR
  branches stay until their pull requests are resolved.

## Recovering or reviewing archived branches

To restore an experimental head after cleanup:

```sh
git fetch origin --tags
git switch -c feature/restored-experiment archive/branches/2026-11-23/feature/hybrid-d8-7427-os
```

Change the suffix to the original name. The original branch is preserved in
full at the archive tag. To inspect without restoration:

```sh
git log --oneline work/pseudo-source-development..archive/branches/2026-11-23/feature/hybrid-d8-7427-os
```

Branch deletion does not rewrite `main`, modify firmware/calibration
values, or merge experimental commits. Keep archive tags until a separate
provenance review explicitly retires them. A clean branch list and passing
source tests do not constitute release or target hardware validation.
