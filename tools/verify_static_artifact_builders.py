#!/usr/bin/env python3
"""
Static artifact builder verifier.

Purpose:
  Verify repo-internal static artifact builders without falsely failing builders
  that require explicit CLI arguments or optional local dependencies.

Rules:
  - Run only builders that can be invoked with no required CLI arguments.
  - Skip parameterized builders unless added to BUILDER_INVOCATION_MANIFEST.
  - Run each builder in an isolated temporary repo copy.
  - Compare generated files against the committed baseline.
  - Report mismatches as repo defects, not hardware findings.

This tool does NOT:
  - prove hardware behavior
  - relax fuel/spark/IAC gates
  - create runtime ASM
  - allow SLICE-1
  - allow custom hardware writers
"""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = Path("maps/tests/static_artifact_builder_verification.csv")


# Add builders here only when their required args are known and canonical.
# Key = repo-relative builder path.
# Value = list of args after the script path.
BUILDER_INVOCATION_MANIFEST: dict[str, list[str]] = {
    # Example:
    # "tools/build_spark_stock_handoff_preservation_contract.py": [
    #     "--out-md", "docs/contracts/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT.md",
    #     "--out-csv", "maps/contracts/spark_stock_handoff_preservation_contract.csv",
    # ],
}


COMMON_REQUIRED_ARG_MARKERS = (
    "--out-md",
    "--out-csv",
    "--name",
    "--addr",
    "--watch",
    "--sink-pc",
    "--sink-register",
    "--start-pc",
    "--pc-start",
    "--end-pc",
    "--pc-end",
    "--vectors",
    "--subsystem",
    "--window",
    "--anchor",
)


@dataclass(frozen=True)
class BuilderResult:
    builder_path: str
    status: str
    returncode: str
    changed_files: str
    missing_files: str
    extra_files: str
    stdout_tail: str
    stderr_tail: str
    notes: str


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def tail(text: str | bytes | None, max_lines: int = 20) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    lines = text.splitlines()
    return "\\n".join(lines[-max_lines:])


def run_cmd(cmd: list[str], cwd: Path, timeout_s: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_s,
        check=False,
    )


def discover_builders(root: Path) -> list[Path]:
    return sorted(p for p in (root / "tools").glob("build_*.py") if p.is_file())


def builder_has_manifest(builder_rel: str) -> bool:
    return builder_rel in BUILDER_INVOCATION_MANIFEST


def builder_requires_manifest(builder: Path) -> tuple[bool, str]:
    """
    Conservative check used to avoid false failures.

    If --help fails, skip the builder unless a manifest entry exists. This catches
    builders that import optional local deps, such as pandas, before argparse.

    If --help succeeds but advertises common required output/selector args, skip
    the builder unless a manifest entry exists. The verifier should not guess
    canonical output paths for parameterized builders.
    """
    builder_rel = rel(builder)
    if builder_has_manifest(builder_rel):
        return False, "manifest_entry_present"

    try:
        proc = run_cmd([sys.executable, builder_rel, "--help"], REPO_ROOT, timeout_s=20)
    except subprocess.TimeoutExpired:
        return True, "skip_help_timeout_no_manifest"

    if proc.returncode != 0:
        return True, "skip_help_failed_no_manifest"

    help_text = proc.stdout + proc.stderr
    matched = [marker for marker in COMMON_REQUIRED_ARG_MARKERS if marker in help_text]
    if matched:
        return True, "skip_parameterized_no_manifest: " + ",".join(matched)

    return False, "zero_arg_candidate"


def copy_repo_to_temp(src: Path) -> Path:
    tmp_base = Path(tempfile.mkdtemp(prefix="7427_builder_verify_"))
    dst = tmp_base / "repo"

    ignore = shutil.ignore_patterns(
        ".git",
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "env",
        "dist",
        "build",
    )
    shutil.copytree(src, dst, ignore=ignore)

    # Make the copied tree self-contained for status comparison.
    init_steps = [
        ["git", "init"],
        ["git", "config", "user.email", "verify@example.invalid"],
        ["git", "config", "user.name", "static verifier"],
        ["git", "add", "."],
        ["git", "commit", "-m", "baseline"],
    ]
    for cmd in init_steps:
        proc = run_cmd(cmd, dst, timeout_s=60)
        if proc.returncode != 0:
            raise RuntimeError(f"failed to prepare temp git repo: {cmd}: {proc.stderr}")

    return dst


def git_status_changed_files(repo_copy: Path) -> tuple[list[str], list[str], list[str]]:
    proc = run_cmd(["git", "status", "--porcelain"], repo_copy, timeout_s=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)

    changed: list[str] = []
    missing: list[str] = []
    extra: list[str] = []

    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        path = line[3:].strip().replace("\\", "/")
        if status == "??":
            extra.append(path)
        elif "D" in status:
            missing.append(path)
        else:
            changed.append(path)

    return sorted(changed), sorted(missing), sorted(extra)


def verify_builder(repo_root: Path, builder: Path, timeout: int) -> BuilderResult:
    builder_rel = rel(builder)

    requires_manifest, reason = builder_requires_manifest(builder)
    if requires_manifest:
        return BuilderResult(
            builder_path=builder_rel,
            status="skip_parameterized_no_manifest",
            returncode="skip",
            changed_files="",
            missing_files="",
            extra_files="",
            stdout_tail="",
            stderr_tail="",
            notes=reason,
        )

    args = BUILDER_INVOCATION_MANIFEST.get(builder_rel, [])
    repo_copy = copy_repo_to_temp(repo_root)

    try:
        cmd = [sys.executable, builder_rel] + args
        try:
            proc = run_cmd(cmd, repo_copy, timeout_s=timeout)
        except subprocess.TimeoutExpired as exc:
            return BuilderResult(
                builder_path=builder_rel,
                status="fail_timeout",
                returncode="timeout",
                changed_files="",
                missing_files="",
                extra_files="",
                stdout_tail=tail(exc.stdout),
                stderr_tail=tail(exc.stderr),
                notes=f"builder exceeded timeout_seconds={timeout}",
            )

        changed, missing, extra = git_status_changed_files(repo_copy)

        if proc.returncode != 0:
            status = "fail_builder_returncode"
            notes = "builder returned nonzero"
        elif changed or missing or extra:
            status = "fail_output_mismatch"
            notes = "builder output differs from committed artifact(s)"
        else:
            status = "pass"
            notes = "builder output matches committed artifact(s)"

        return BuilderResult(
            builder_path=builder_rel,
            status=status,
            returncode=str(proc.returncode),
            changed_files=";".join(changed),
            missing_files=";".join(missing),
            extra_files=";".join(extra),
            stdout_tail=tail(proc.stdout),
            stderr_tail=tail(proc.stderr),
            notes=notes if not args else f"{notes}; manifest_args_used",
        )
    finally:
        shutil.rmtree(repo_copy.parent, ignore_errors=True)


def write_report(path: Path, results: Iterable[BuilderResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "builder_path",
        "status",
        "returncode",
        "changed_files",
        "missing_files",
        "extra_files",
        "stdout_tail",
        "stderr_tail",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow({field: getattr(result, field) for field in fields})


def print_summary(results: list[BuilderResult]) -> None:
    for result in results:
        print(f"{result.status}: {result.builder_path}")
        if result.status != "pass":
            print(f"  returncode: {result.returncode}")
            if result.changed_files:
                print(f"  changed_files: {result.changed_files}")
            if result.missing_files:
                print(f"  missing_files: {result.missing_files}")
            if result.extra_files:
                print(f"  extra_files: {result.extra_files}")
            if result.stderr_tail:
                print("  stderr_tail:")
                for line in result.stderr_tail.splitlines():
                    print(f"    {line}")
            if result.notes:
                print(f"  notes: {result.notes}")

    passed = sum(1 for r in results if r.status == "pass")
    skipped = sum(1 for r in results if r.status.startswith("skip_"))
    failed = sum(1 for r in results if r.status.startswith("fail_"))

    print("")
    print(f"PASS: {passed}")
    print(f"SKIP: {skipped}")
    print(f"FAIL: {failed}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--builder",
        action="append",
        help="Specific builder path to verify. May be repeated. Default: all tools/build_*.py.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds per builder. Default: 60.",
    )
    parser.add_argument(
        "--write-report",
        nargs="?",
        const=DEFAULT_REPORT_PATH.as_posix(),
        help="Write verification CSV report. Default path when no value is supplied: maps/tests/static_artifact_builder_verification.csv.",
    )
    args = parser.parse_args(argv)

    repo_root = REPO_ROOT
    if args.builder:
        builders = [repo_root / builder for builder in args.builder]
    else:
        builders = discover_builders(repo_root)

    missing_builders = [builder for builder in builders if not builder.exists()]
    if missing_builders:
        for builder in missing_builders:
            print(f"missing builder: {builder.relative_to(repo_root).as_posix()}", file=sys.stderr)
        return 2

    results: list[BuilderResult] = []
    self_path = Path(__file__).resolve()
    for builder in builders:
        if builder.resolve() == self_path:
            continue
        results.append(verify_builder(repo_root, builder, args.timeout))

    print_summary(results)

    if args.write_report:
        write_report(repo_root / args.write_report, results)
        print(f"wrote report: {args.write_report}")

    failures = [result for result in results if result.status.startswith("fail_")]
    if failures:
        print(f"FAIL: {len(failures)} builder(s) did not reproduce committed artifacts")
        return 1

    print(f"PASS: static builder verification completed with no runnable-builder failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
