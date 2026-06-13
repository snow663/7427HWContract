#!/usr/bin/env python3
"""Build the stock driver preservation policy contract artifacts.

This builder records the project-level rule for when a subsystem can avoid
per-register ASIC bench discovery by preserving a complete stock hardware-driver
routine. It does not create runtime code, hardware writers, or implementation
ASM.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROWS = [
    {
        "policy_id": "STOCK-DRV-001",
        "topic": "preserved_stock_driver_definition",
        "classification": "static_proof_gated",
        "required_proof": "complete stock hardware-driver routine range identified and preserved",
        "allowed": "clean OS may call preserved stock driver after feeding required stock-compatible state",
        "blocked": "partial routine copy or undocumented deletion of stock side effects",
        "notes": "Preservation means behavior-for-behavior, not guessed register semantics.",
    },
    {
        "policy_id": "STOCK-DRV-002",
        "topic": "input_state_seeding",
        "classification": "required_static_proof",
        "required_proof": "all RAM inputs, calculated state, flags, period bases, rolling anchors, and mode bits required by preserved driver are identified and seeded",
        "allowed": "clean calculation may feed stock-compatible variables",
        "blocked": "calling preserved driver with unseeded or incompatible state",
        "notes": "This is the main seam between clean OS logic and preserved hardware driver.",
    },
    {
        "policy_id": "STOCK-DRV-003",
        "topic": "side_effects_order_delay",
        "classification": "required_static_proof",
        "required_proof": "write order, delay calls, interrupt assumptions, mirror/ack behavior, monitor flags, and rolling-state updates are preserved",
        "allowed": "preserved routine owns its original hardware side effects",
        "blocked": "reordering writes, removing delay calls, deleting monitor or mirror side effects",
        "notes": "Physical meaning may be deferred, but behavioral sequence may not be changed.",
    },
    {
        "policy_id": "STOCK-DRV-004",
        "topic": "custom_direct_writer",
        "classification": "blocked_bench_required",
        "required_proof": "bench proof of register semantics, timing windows, safety state, and output behavior",
        "allowed": "none before bench proof",
        "blocked": "new direct ASIC writer, simplified raw-register writer, or bypass of stock driver",
        "notes": "A custom writer cannot inherit the stock driver proof.",
    },
    {
        "policy_id": "STOCK-DRV-005",
        "topic": "physical_register_semantics",
        "classification": "deferred_bench_optional_for_preservation",
        "required_proof": "not required before using complete preserved stock driver",
        "allowed": "document physical ASIC semantics as deferred when stock behavior is preserved",
        "blocked": "claiming physical meaning without trace or bench evidence",
        "notes": "Deferred semantics do not block preservation; they do block custom writers.",
    },
    {
        "policy_id": "STOCK-DRV-006",
        "topic": "fuel_policy",
        "classification": "bench_required_unless_stock_driver_preserved",
        "required_proof": "direct compact $3FCE path needs bench proof unless entire stock fuel output/scheduler driver is preserved",
        "allowed": "bench-proven direct $3FCE path or complete preserved stock fuel driver",
        "blocked": "engine-runnable direct fuel path without proof or preservation",
        "notes": "Current SLICE-0 fuel path remains bench-proof gated.",
    },
    {
        "policy_id": "STOCK-DRV-007",
        "topic": "spark_policy",
        "classification": "stock_preservation_allowed_after_static_contract",
        "required_proof": "preserve stock spark ASIC handoff routine and feed stock-compatible spark state",
        "allowed": "clean spark state -> preserved stock handoff routine",
        "blocked": "custom direct spark ASIC writer or simplified raw-angle writer",
        "notes": "Spark physical semantics are deferred; stock handoff is the hardware driver.",
    },
    {
        "policy_id": "STOCK-DRV-008",
        "topic": "iac_policy",
        "classification": "bench_required_unless_stock_driver_preserved",
        "required_proof": "direct A/B/Enable/park writer needs bench proof unless stock IAC driver is preserved complete",
        "allowed": "bench-proven direct IAC writer or complete preserved stock IAC driver",
        "blocked": "custom IAC phase/enable writer without bench proof",
        "notes": "IAC can use the same preservation logic only if the stock driver is preserved as a black box.",
    },
    {
        "policy_id": "STOCK-DRV-009",
        "topic": "runtime_validation",
        "classification": "still_required",
        "required_proof": "eventual real-hardware validation before trusting engine operation",
        "allowed": "static-preserved stock driver can proceed to integration planning",
        "blocked": "claiming final engine safety solely from static preservation",
        "notes": "Static preservation changes the discovery gate, not the final validation requirement.",
    },
]

FIELDS = ["policy_id", "topic", "classification", "required_proof", "allowed", "blocked", "notes"]

CONTRACT_MD = """# Stock Driver Preservation Policy\n\n## Purpose\n\nDefine when a subsystem can bypass per-register ASIC bench discovery by preserving the stock hardware-driver routine.\n\nThis policy prevents contradictions between fuel, spark, and IAC as the project shifts from trying to understand every ASIC register physically to preserving proven stock hardware drivers where practical.\n\nThis policy does not create runtime code, hardware writer ASM, or subsystem implementation.\n\n## Core Rule\n\n```text\nPreserved stock driver:\n  static completeness proof required\n  input/state seeding proof required\n  side effects/order/delay proof required\n  no physical per-register proof required before use\n\nCustom direct writer:\n  bench proof required\n```\n\n## Required Static Proof for a Preserved Stock Driver\n\nA preserved stock driver may be used as the hardware authority only if all of the following are true:\n\n```text\n1. Complete stock hardware-driver routine range is identified.\n2. All required input RAM/calculated state is identified.\n3. All required flags, mode bits, period bases, rolling anchors, and companion state are identified.\n4. All ASIC-facing writes performed by the preserved routine are identified.\n5. Write order is preserved.\n6. Delay calls and timing/interrupt assumptions are preserved.\n7. Mirror/ack/status behavior is preserved.\n8. Monitor and fault side effects are preserved.\n9. First-event, reset, dropout, and restart seed states are initialized safely.\n10. No alternate custom direct writer exists for the same hardware function.\n```\n\n## What Preservation Bypasses\n\nFor a complete preserved stock hardware driver, the project does not need to bench-discover the physical meaning of each ASIC register before using the preserved path.\n\nAllowed deferral:\n\n```text\nexact physical meaning of individual ASIC registers\ninternal ASIC latch/compare semantics\nwhether a value is ack, mirror, diagnostic, rolling state, or direct output\n```\n\nThe reason is narrow: the stock routine is treated as the already-proven hardware driver. The proof burden shifts to preserving that routine completely and feeding it compatible state.\n\n## What Preservation Does Not Bypass\n\nPreservation does not bypass:\n\n```text\nstatic proof of complete routine range\nstatic proof of input/state seeding\nstatic proof of side effects/order/delay preservation\nstatic proof of safe reset/first-event/dropout state\neventual real-hardware validation before trusting engine operation\n```\n\n## Custom Direct Writer Rule\n\nA custom direct writer cannot inherit the stock driver proof.\n\nAny new direct ASIC writer requires bench proof of:\n\n```text\nregister semantics\nunit conversion\nwrite timing/window\nwrite order\nlatch/commit behavior\nsafety/default state\nphysical output behavior\ndropout/restart behavior\n```\n\n## Current Subsystem Classification\n\n```text\nfuel:\n  bench_required_unless_stock_driver_preserved\n  current compact $3FCE path remains bench-proof gated\n\nspark:\n  stock_preservation_allowed_after_static_contract\n  clean spark state -> preserved stock handoff routine\n  custom direct spark writer remains blocked/bench-required\n  physical spark ASIC semantics deferred, not blocking\n\niac:\n  bench_required_unless_stock_driver_preserved\n  custom A/B/Enable/park writer remains bench-required\n  stock-driver preservation may reclassify IAC if complete stock IAC driver is preserved\n```\n\n## Label Policy\n\n```text\ncustom_direct_writer:\n  blocked_bench_required\n\nstock_driver_preservation:\n  allowed_after_static_contract\n\nphysical_register_semantics:\n  deferred_bench_optional_for_preservation\n  required_for_custom_writer\n```\n\n## Guardrails\n\nAllowed:\n\n```text\nclean OS calculates desired state\nclean OS feeds stock-compatible state variables\npreserved stock driver owns hardware-facing writes\nphysical per-register semantics are documented as deferred\n```\n\nBlocked:\n\n```text\npartial stock driver copy treated as complete\nunseeded state entering preserved stock driver\ncustom direct ASIC writer without bench proof\nsimplified raw-register writer without bench proof\ndeleting rolling state, mirror/ack behavior, monitor flags, or delay assumptions\nclaiming physical register meaning without trace or bench evidence\nclaiming final engine safety solely from static preservation\n```\n"""

TEST_MD = """# Stock Driver Preservation Policy Test\n\n## Goal\n\nVerify that the repo-level stock-driver preservation policy clearly separates preserved stock hardware drivers from custom direct ASIC writers.\n\nThis is a static policy contract only. It must not create runtime ASM, subsystem implementation, custom writers, or bench result claims.\n\n## Required Files\n\n```text\ntools/build_stock_driver_preservation_policy.py\ndocs/contracts/STOCK_DRIVER_PRESERVATION_POLICY.md\nmaps/contracts/stock_driver_preservation_policy.csv\n```\n\n## Required Checks\n\n| Test | Expected |\n|---|---|\n| preserved stock driver rule | static completeness/input/side-effect proof required |\n| custom direct writer rule | bench proof required |\n| physical semantics rule | deferred for complete preservation, required for custom writer |\n| fuel classification | bench-required unless stock fuel driver is preserved |\n| spark classification | stock handoff preservation allowed after static contract |\n| IAC classification | bench-required unless stock IAC driver is preserved |\n| implementation boundary | no runtime ASM or writer created |\n| final validation boundary | real-hardware validation still required before trusting engine operation |\n\n## Required CSV Rows\n\n```text\nSTOCK-DRV-001 preserved_stock_driver_definition\nSTOCK-DRV-002 input_state_seeding\nSTOCK-DRV-003 side_effects_order_delay\nSTOCK-DRV-004 custom_direct_writer\nSTOCK-DRV-005 physical_register_semantics\nSTOCK-DRV-006 fuel_policy\nSTOCK-DRV-007 spark_policy\nSTOCK-DRV-008 iac_policy\nSTOCK-DRV-009 runtime_validation\n```\n\n## Pass Criteria\n\n```text\nPASS:\n  policy separates preserved stock driver from custom direct writer.\n  preserved stock driver requires static completeness proof.\n  custom direct writer requires bench proof.\n  spark can use preserved stock handoff after static contract.\n  fuel remains bench-proof gated unless stock fuel driver is preserved.\n  IAC remains bench-proof gated unless stock IAC driver is preserved.\n  physical ASIC semantics are deferred only for complete preserved stock drivers.\n  no implementation files are created by this policy.\n```\n\n## Fail / Rework Criteria\n\n```text\nREWORK:\n  policy permits custom direct writer without bench proof.\n  policy treats partial stock routine copy as complete preservation.\n  policy lets physical semantics deferral justify custom writes.\n  policy claims final engine safety from static preservation alone.\n  policy creates runtime ASM, hardware writer, or implementation code.\n```\n"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ROWS)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    write_text(root / "docs/contracts/STOCK_DRIVER_PRESERVATION_POLICY.md", CONTRACT_MD)
    write_csv(root / "maps/contracts/stock_driver_preservation_policy.csv")
    write_text(root / "docs/tests/STOCK_DRIVER_PRESERVATION_POLICY_TEST.md", TEST_MD)
    print("wrote stock driver preservation policy artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
