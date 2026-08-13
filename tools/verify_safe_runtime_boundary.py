#!/usr/bin/env python3
"""Verify the first 7427 replacement-OS safe runtime cannot touch hardware or enable actuators."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "source/replacement_os/core/safe_runtime.asm"
ABI = ROOT / "source/replacement_os/include/runtime_abi.inc"

PERMS = ["PERM_FUEL", "PERM_SPARK", "PERM_IAC", "PERM_PUMP", "PERM_AUX"]
VALIDS = [
    "CMD_FUEL_VALID",
    "CMD_SPARK_VALID",
    "CMD_IAC_MOTION_VALID",
    "CMD_PUMP_VALID",
    "CMD_AUX_VALID",
]


def fail(msg: str) -> None:
    raise SystemExit("FAIL: " + msg)


def main() -> int:
    core = CORE.read_text(encoding="utf-8")
    abi = ABI.read_text(encoding="utf-8")

    # Core cannot contain direct relocated CPU/ASIC hardware addresses or stock
    # L3xxx register symbols. Semantic constants in the ABI are allowed.
    direct_addr = re.findall(r"\$3[0-9A-Fa-f]{3}", core)
    direct_sym = re.findall(r"\bL3[0-9A-Fa-f]{3}\b", core)
    if direct_addr:
        fail(f"hardware-like direct address found in core: {sorted(set(direct_addr))}")
    if direct_sym:
        fail(f"hardware-like L3xxx symbol found in core: {sorted(set(direct_sym))}")

    # Every permission must be explicitly cleared at initialization and in the
    # common disable routine. A permission-enable token may be compared but the
    # safe core is forbidden from writing it into any permission variable.
    for perm in PERMS:
        if f"STAA    {perm}" not in core:
            fail(f"safe-init zero store missing for {perm}")
        if f"CLR     {perm}" not in core:
            fail(f"common disable clear missing for {perm}")

    enable_store = re.search(
        r"LDAA\s+#PERMISSION_ENABLED.{0,120}STAA\s+PERM_",
        core,
        re.S,
    )
    if enable_store:
        fail("safe core contains a path that writes PERMISSION_ENABLED to a permission")

    for flag in VALIDS:
        if f"CLR     {flag}" not in core:
            fail(f"inactive command-valid clear missing for {flag}")

    required_routines = [
        "OS_SAFE_INIT:",
        "OS_TICK_6P25MS:",
        "OS_REF_EVENT:",
        "OS_FORCE_DROPOUT:",
        "OS_KEYOFF_EVENT:",
        "OS_ARBITRATE_COMMANDS:",
        "OS_DISABLE_ALL_ACTUATORS:",
        "OS_ZERO_ALL_COMMANDS:",
        "OS_DEBUG_SNAPSHOT_TICK:",
    ]
    for name in required_routines:
        if name not in core:
            fail(f"required safe-runtime routine missing: {name}")

    if "PERMISSION_ENABLED      EQU     $A5" not in abi:
        fail("deliberate non-boolean permission token missing from ABI")

    print("PASS: safe runtime contains no direct $3xxx/L3xxx hardware access")
    print("PASS: all production permissions boot clear and have common clear paths")
    print("PASS: safe core contains no permission-enable store")
    print("PASS: all HAL command-valid flags have inactive clear paths")
    print("PASS: lifecycle/arbitration/debug safe-runtime entry points present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
