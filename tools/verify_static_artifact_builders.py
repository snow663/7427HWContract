#!/usr/bin/env python3
"""
Verify committed static-artifact builders against their committed outputs.

This tool is intentionally repo-internal consistency checking only. It does not
prove hardware behavior, does not relax any subsystem gate, and does not create
runtime ASM. It runs builders in temporary repository copies, compares the
post-build tree against the committed working tree, and reports any mismatches
as repo defects.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
}

IGNORE_SUFFIXES = {
    ".pyc",
    ".pyo",
}

DEFAULT_REPORT_PATH = Path("maps/tests/static_artifact_builder_verification.csv")


@dataclass(frozen=True)
class BuilderResult:
    builder_path: str
    status: str
    returncode: int
    changed_files: str
    missing_files: str
    extra_files: str
    stdout_tail: str
    stderr_tail: str
    notes: str


def is_ignored(path: Path) -> bool:
    parts = set(path.parts)
    if parts & IGNORE_DIRS:
        return True
    if path.suffix in IGNORE_SUFFIXES:
        return True
    return False


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if is_ignored(rel):
            continue
        if path.is_file():
            out[rel.as_posix()] = sha256_file(path)
    return out


def copy_repo_to_temp(src: Path, dst: Path) -> None:
    def ignore(dir_path: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            candidate = Path(dir_path, name)
            rel = candidate.relative_to(src) if candidate.is_relative_to(src) else Path(name)
            if name in IGNORE_DIRS or is_ignored(rel):
                ignored.add(name)
        return ignored

    shutil.copytree(src, dst, ignore=ignore)


def discover_builders(root: Path) -> list[Path]:
    tools = root / "tools"
    builders = sorted(p for p in tools.glob("build_*.py") if p.is_file())
    return builders


def tail(text: str, max_lines: int = 20) -> str:
    lines = text.splitlines()
    return "\\n".join(lines[-max_lines:])


def run_builder_in_copy(repo_root: Path, builder_rel: Path, timeout: int) -> BuilderResult:
    with tempfile.TemporaryDirectory(prefix="7427_builder_verify_") as td:
        temp_root = Path(td) / "repo"
        copy_repo_to_temp(repo_root, temp_root)

        before = tree_hashes(temp_root)
        cmd = [sys.executable, builder_rel.as_posix()]

        try:
            proc = subprocess.run(
                cmd,
                cwd=temp_root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return BuilderResult(
                builder_path=builder_rel.as_posix(),
                status="fail_timeout",
                returncode=-1,
                changed_files="",
                missing_files="",
                extra_files="",
                stdout_tail=tail(exc.stdout or ""),
                stderr_tail=tail(exc.stderr or ""),
                notes=f"builder exceeded timeout_seconds={timeout}",
            )

        after = tree_hashes(temp_root)
        expected = tree_hashes(repo_root)

        changed = sorted(
            rel
            for rel in set(before) | set(after)
            if before.get(rel) != after.get(rel)
        )
        missing = sorted(rel for rel in expected if rel not in after)
        extra = sorted(rel for rel in after if rel not in expected)
        mismatched = sorted(
            rel
            for rel in expected.keys() & after.keys()
            if expected[rel] != after[rel]
        )

        if proc.returncode != 0:
            status = "fail_builder_returncode"
        elif missing or extra or mismatched:
            status = "fail_output_mismatch"
        else:
            status = "pass"

        notes_parts: list[str] = []
        if changed:
            notes_parts.append("temp tree changed during builder run")
        if mismatched:
            notes_parts.append("generated output differs from committed file(s)")
        if extra:
            notes_parts.append("builder generated file(s) absent from repo")
        if missing:
            notes_parts.append("builder deleted committed file(s) in temp copy")
        if not notes_parts:
            notes_parts.append("builder output matches committed tree")

        return BuilderResult(
            builder_path=builder_rel.as_posix(),
            status=status,
            returncode=proc.returncode,
            changed_files=";".join(changed),
            missing_files=";".join(missing),
            extra_files=";".join(extra),
            stdout_tail=tail(proc.stdout),
            stderr_tail=tail(proc.stderr),
            notes="; ".join(notes_parts),
        )


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
        for r in results:
            writer.writerow({field: getattr(r, field) for field in fields})


def print_summary(results: list[BuilderResult]) -> None:
    for r in results:
        print(f"{r.status}: {r.builder_path}")
        if r.status != "pass":
            print(f"  returncode: {r.returncode}")
            if r.changed_files:
                print(f"  changed_files: {r.changed_files}")
            if r.missing_files:
                print(f"  missing_files: {r.missing_files}")
            if r.extra_files:
                print(f"  extra_files: {r.extra_files}")
            if r.stderr_tail:
                print("  stderr_tail:")
                for line in r.stderr_tail.splitlines():
                    print(f"    {line}")


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

    repo_root = repo_root_from_script()
    if args.builder:
        builders = [repo_root / b for b in args.builder]
    else:
        builders = discover_builders(repo_root)

    missing_builders = [b for b in builders if not b.exists()]
    if missing_builders:
        for b in missing_builders:
            print(f"missing builder: {b.relative_to(repo_root).as_posix()}", file=sys.stderr)
        return 2

    results: list[BuilderResult] = []
    for builder in builders:
        rel = builder.relative_to(repo_root)
        if rel.as_posix() == Path(__file__).relative_to(repo_root).as_posix():
            continue
        results.append(run_builder_in_copy(repo_root, rel, args.timeout))

    print_summary(results)

    if args.write_report:
        write_report(repo_root / args.write_report, results)
        print(f"wrote report: {args.write_report}")

    failures = [r for r in results if r.status != "pass"]
    if failures:
        print(f"FAIL: {len(failures)} builder(s) did not reproduce committed artifacts")
        return 1

    print(f"PASS: {len(results)} static artifact builder(s) reproduce committed artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
