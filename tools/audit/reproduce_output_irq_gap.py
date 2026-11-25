#!/usr/bin/env python3
"""Compile actual production C and run the intentionally red OC4/OC5 witness.

No simulator, target ISA oracle, or substitute IRQ implementation is involved.
Expected on the audited base: exit1, two PCM_UNIMPLEMENTED/no-acknowledgment
failures. A host C compiler is required. Compilation/link failure is not a
successful reproduction. This is deliberately outside the green schema tests.
"""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    sources = sorted((ROOT / "pseudo-source/src").rglob("*.c"))
    sources += sorted((ROOT / "pseudo-source/calibration").glob("*.c"))
    sources += [ROOT / "pseudo-source/platform/hc11_vector_contract.c",
                ROOT / "tests/audit/output_irq_readiness_probe.c"]
    with tempfile.TemporaryDirectory(prefix="7427-output-irq-audit-") as temporary:
        binary = Path(temporary) / "output_irq_probe"
        command = [*shlex.split(os.environ.get("CC", "cc")), "-std=c11", "-O0",
                   "-I", str(ROOT / "pseudo-source/include"),
                   *(str(source) for source in sources), "-o", str(binary)]
        subprocess.run(command, check=True)
        return subprocess.run([str(binary)], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
