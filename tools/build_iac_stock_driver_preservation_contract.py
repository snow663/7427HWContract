#!/usr/bin/env python3
"""Build the IAC stock-driver preservation contract artifacts.

This script emits a static decision seam only. It does not generate runtime ASM,
IAC output code, bench hooks, or a custom A/B/Enable/park writer.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/contracts/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT.md"
CSV_PATH = ROOT / "maps/contracts/iac_stock_driver_preservation_contract.csv"
TEST_PATH = ROOT / "docs/tests/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT_TEST.md"

ROWS = [
    {
        "gate_id": "IAC-STOCK-001",
        "category": "driver_range",
        "requirement": "Identify the complete preserved stock IAC hardware-driver routine range before accepting stock-driver preservation.",
        "current_status": "defined_not_proven",
        "source_anchor": "candidate: setup around L925E; reset/park around L93E1-L940A; phase/output behavior around LF405 and LFB14-LFB69",
        "blocking_if_incomplete": "yes",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "Partial source anchoring is not enough to accept preservation. The complete output-driver range and call context must be pinned.",
    },
    {
        "gate_id": "IAC-STOCK-002",
        "category": "input_state",
        "requirement": "Identify all required stock-compatible IAC input RAM/state variables that the clean OS must seed before calling the preserved driver.",
        "current_status": "defined_not_proven",
        "source_anchor": "known candidates include L0007 present motor position, L0008 IAC command/target, L0009 IAC/reset mode bits, L000A phase/state bits, L004B/L004C port shadows, L0036/L003B/L004F condition flags, L0862/L0871/L0873/L0875 support state",
        "blocking_if_incomplete": "yes",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "A preserved driver cannot be accepted with unseeded position, reset, phase, park, port-shadow, or idle-mode state.",
    },
    {
        "gate_id": "IAC-STOCK-003",
        "category": "hardware_writes",
        "requirement": "List every hardware-facing IAC-related write performed by the preserved stock driver and prove the clean OS does not write those directly outside the preserved path.",
        "current_status": "defined_not_proven",
        "source_anchor": "known writes include L3062 I/O port D writes, L3060 port writes, L3FFC I/O D port strobe writes, and possible port-shadow transfers through LF405/LFB14/LFB39",
        "blocking_if_incomplete": "yes",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "Physical meanings of individual port bits may be deferred only if the full stock driver is preserved complete.",
    },
    {
        "gate_id": "IAC-STOCK-004",
        "category": "order_delay_interrupt_side_effects",
        "requirement": "Preserve stock write order, delay calls, interrupt assumptions, port-shadow side effects, and major-loop/segment timing assumptions.",
        "current_status": "defined_not_proven",
        "source_anchor": "candidate output cycling/port code around LFB14-LFB69 includes L3062 updates, SEI, delay call LFBD6, and L3FFC strobes; stock production driver range still must be separated from test/output-cycling code",
        "blocking_if_incomplete": "yes",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "Changing port write order, phase update cadence, or interrupt windows converts preservation into a custom driver.",
    },
    {
        "gate_id": "IAC-STOCK-005",
        "category": "reset_park_dropout_state",
        "requirement": "Prove first-event, reset-in-work, bad-shutdown, park, ignition-off, and dropout/unsafe IAC states are initialized safely before the preserved driver is trusted.",
        "current_status": "defined_not_proven",
        "source_anchor": "L925E setup seeds parked position from L4EB0 into L0007; L93E1-L940A handles reset-in-work, zero position, run/start request, ignition-off, park, and engine-running branches",
        "blocking_if_incomplete": "yes",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "Stock-driver preservation must include safe park/reset behavior, not only normal closed-loop stepping.",
    },
    {
        "gate_id": "IAC-STOCK-006",
        "category": "no_alternate_writer",
        "requirement": "Prove no alternate custom direct IAC writer exists and no clean-OS path writes L3062/L3060/L3FFC for IAC outside the preserved stock driver.",
        "current_status": "defined_not_proven",
        "source_anchor": "repo policy hard boundary: no direct L3062 writer without bench proof or complete stock-driver preservation",
        "blocking_if_incomplete": "yes",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "A custom direct A/B/Enable/park writer remains bench-required.",
    },
    {
        "gate_id": "IAC-STOCK-007",
        "category": "physical_semantics",
        "requirement": "Mark physical IAC port-bit semantics as deferred, not blocking, only if the complete stock IAC driver is preserved behavior-for-behavior.",
        "current_status": "defined_not_proven",
        "source_anchor": "L3062/L3060/L3FFC physical meanings remain unresolved for custom direct use",
        "blocking_if_incomplete": "yes_for_preservation_acceptance",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "Deferred semantics do not authorize simplified direct port writes.",
    },
    {
        "gate_id": "IAC-STOCK-DECISION",
        "category": "decision",
        "requirement": "Decide whether stock IAC driver preservation can supersede custom A/B/Enable/park bench proof.",
        "current_status": "contract_defined_preservation_not_proven",
        "source_anchor": "this contract",
        "blocking_if_incomplete": "yes",
        "active_route_if_incomplete": "custom_iac_writer_bench_required",
        "notes": "Allowed final decisions: accepted_static_route, incomplete_custom_bench_route_required, rejected_custom_bench_route_required.",
    },
]


def emit_csv() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(ROWS)


def emit_contract() -> None:
    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(
        """# IAC Stock Driver Preservation Contract\n\n"
        "Purpose: decide whether IAC can bypass physical A/B/Enable/park bench proof by preserving the complete stock IAC hardware-driver routine.\n\n"
        "This is a static decision seam only. It does not implement IAC code, does not create a direct IAC writer, and does not relax the bench requirement for any custom A/B/Enable/park writer.\n\n"
        "## Current decision\n\n"
        "```text\n"
        "iac_stock_driver_preservation:\n"
        "  contract_defined_preservation_not_proven\n\n"
        "custom_iac_writer:\n"
        "  bench_required\n\n"
        "active_iac_route_if_work_resumes:\n"
        "  no custom direct IAC writer without bench proof\n"
        "  or complete stock IAC driver preservation proof first\n"
        "```\n\n"
        "## Authority model\n\n"
        "If stock IAC driver preservation is eventually accepted:\n\n"
        "```text\n"
        "clean idle-air decision\n"
        "→ stock-compatible IAC state\n"
        "→ preserved stock IAC output driver\n"
        "→ stock routine owns A/B/Enable/phase/park behavior\n"
        "```\n\n"
        "If preservation is incomplete or rejected:\n\n"
        "```text\n"
        "custom direct A/B/Enable/park writer\n"
        "→ physical bench proof required before use\n"
        "```\n\n"
        "## Required gates\n\n"
        + "\n".join(f"- `{row['gate_id']}`: {row['requirement']}" for row in ROWS) +
        "\n\n## Source-trace anchors currently known\n\n"
        "```text\n"
        "L925E setup candidate:\n"
        "  seeds IAC setup/park-related state, including L4EB0 -> L0007\n\n"
        "L93E1-L940A reset/park candidate:\n"
        "  reset-in-work, zero-position, run/start request, ignition-off, park, engine-running branches\n\n"
        "L9B10 / L9BD6 position update candidates:\n"
        "  decrement/increment L0007 present motor position\n\n"
        "LF405 / LFB14-LFB69 port-output candidates:\n"
        "  L3062 / L3060 / L3FFC interactions, port-shadow and strobe behavior\n"
        "```\n\n"
        "These anchors do not prove complete stock-driver preservation. They only define starting points for a later static proof index.\n\n"
        "## Explicit non-claims\n\n"
        "```text\n"
        "This contract does not claim physical meaning of each L3062/L3060/L3FFC bit.\n"
        "This contract does not prove the complete stock IAC driver range.\n"
        "This contract does not authorize a custom direct IAC writer.\n"
        "This contract does not bypass IAC bench proof for custom A/B/Enable/park output.\n"
        "This contract does not create runtime ASM.\n"
        "```\n\n"
        "## Decision outcomes\n\n"
        "```text\n"
        "iac_stock_driver_preservation:\n"
        "  accepted_static_route\n\n"
        "iac_stock_driver_preservation:\n"
        "  incomplete_custom_bench_route_required\n\n"
        "iac_stock_driver_preservation:\n"
        "  rejected_custom_bench_route_required\n"
        "```\n\n"
        "Current outcome is `contract_defined_preservation_not_proven`; therefore custom direct IAC hardware output remains bench-gated.\n",
        encoding="utf-8",
    )


def emit_test() -> None:
    TEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_PATH.write_text(
        """# IAC Stock Driver Preservation Contract Test\n\n"
        "This test defines acceptance criteria for the static IAC preservation contract. It is not a runtime or bench test.\n\n"
        "## Required files\n\n"
        "```text\n"
        "tools/build_iac_stock_driver_preservation_contract.py\n"
        "docs/contracts/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT.md\n"
        "maps/contracts/iac_stock_driver_preservation_contract.csv\n"
        "docs/tests/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT_TEST.md\n"
        "```\n\n"
        "## Static assertions\n\n"
        "The contract must state:\n\n"
        "```text\n"
        "IAC stock-driver preservation is only a candidate route.\n"
        "Current decision is contract_defined_preservation_not_proven.\n"
        "Custom direct A/B/Enable/park writer remains bench-required.\n"
        "No IAC implementation is emitted.\n"
        "No direct L3062/L3060/L3FFC writer is authorized outside a proven preserved stock driver.\n"
        "Physical port-bit semantics may be deferred only for complete stock-driver preservation.\n"
        "```\n\n"
        "## Required gate rows\n\n"
        "The CSV must include:\n\n"
        "```text\n"
        "IAC-STOCK-001 complete preserved driver range\n"
        "IAC-STOCK-002 required input/state seeding\n"
        "IAC-STOCK-003 hardware-facing writes\n"
        "IAC-STOCK-004 order/delay/interrupt/side effects\n"
        "IAC-STOCK-005 reset/park/dropout state\n"
        "IAC-STOCK-006 no alternate custom writer\n"
        "IAC-STOCK-007 physical semantics deferred only if preserved complete\n"
        "IAC-STOCK-DECISION current decision\n"
        "```\n\n"
        "## Fail conditions\n\n"
        "The contract fails if it:\n\n"
        "```text\n"
        "marks IAC stock-driver preservation accepted without a later static proof index\n"
        "authorizes custom direct L3062/L3060/L3FFC writes\n"
        "claims physical A/B/Enable/park bit meanings without bench or trace evidence\n"
        "emits runtime ASM\n"
        "relaxes bench proof for custom direct IAC hardware output\n"
        "treats partial stock source anchors as a complete preserved driver\n"
        "```\n",
        encoding="utf-8",
    )


def main() -> None:
    emit_csv()
    emit_contract()
    emit_test()
    print(f"wrote {CONTRACT_PATH.relative_to(ROOT)}")
    print(f"wrote {CSV_PATH.relative_to(ROOT)}")
    print(f"wrote {TEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
