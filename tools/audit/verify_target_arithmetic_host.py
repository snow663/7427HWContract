#!/usr/bin/env python3
"""Build actual host C contract executables after target-width corrections.

This checks host behavior only. It neither supplies nor impersonates an HC11
compiler. No CMake installation is required. AUDIT_REPO selects a baseline.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import subprocess
import tempfile


def verify(repo, output, jobs):
    root = repo / "pseudo-source"
    files = sorted([*root.joinpath("src").rglob("*.c"), *root.joinpath("calibration").rglob("*.c")])
    compiler = os.environ.get("CC", "cc")

    def compile_one(path):
        obj = output / (str(path.relative_to(root)).replace("/", "_") + ".o")
        args = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
                "-I", str(root / "include"), "-c", str(path), "-o", str(obj)]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(str(path) + "\n" + result.stderr)
        return str(obj)

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        objects = list(pool.map(compile_one, files))
    library = output / "libpcm.a"
    subprocess.run([os.environ.get("AR", "ar"), "rcs", str(library), *objects], check=True)
    print(f"Compiled {len(files)} production C translation units with -Werror (HOST only).")
    for name in ("fuel_mixture", "fuel_feedback", "fuel_delivery", "boot_controllers", "fuel_governor_compute"):
        exe = output / name
        subprocess.run([compiler, "-std=c11", "-O2", "-I", str(root / "include"),
                        str(root / "tests" / (name + "_test.c")), str(library), "-o", str(exe)], check=True)
        result = subprocess.run([str(exe), "--contracts"], check=True, capture_output=True, text=True)
        print(name + ": " + result.stdout.strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(os.environ.get("AUDIT_REPO", Path(__file__).resolve().parents[2])))
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="7427-arithmetic-host-") as work:
        verify(args.repo.resolve(), Path(work), args.jobs)
