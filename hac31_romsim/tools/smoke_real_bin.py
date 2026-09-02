#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from romsim.simulator import Simulator, StopReason


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real $31 BIN through reset/startup")
    parser.add_argument("binfile")
    parser.add_argument("--instructions", type=int, default=100_000)
    parser.add_argument("--scenario")
    parser.add_argument("--trace-out")
    args = parser.parse_args()

    sim = Simulator.from_profile_file(ROOT / "romsim" / "profiles" / "gm_16197427_31.json")
    sim.load_bin(args.binfile)
    if args.scenario:
        sim.load_scenario(args.scenario)
    if args.trace_out:
        sim.trace.start_stream(args.trace_out)
    sim.reset()
    result = sim.run(max_instructions=args.instructions)
    sim.trace.close_stream()
    print(sim.image_summary())
    print(sim.summary())
    print(f"stop={result.reason.value} detail={result.detail or '-'} cycles={result.cycles}")
    print(f"outputs={len(sim.trace.outputs)} bus_records_in_memory={len(sim.trace.accesses)}")
    print(f"fuel_3FCE={sum(row.address == 0x3FCE for row in sim.trace.outputs)}")
    print(f"unknown_306x={sum(row.evidence == 'contract_test_item' for row in sim.trace.outputs)}")
    return 1 if result.reason == StopReason.UNKNOWN_OPCODE else 0


if __name__ == "__main__":
    raise SystemExit(main())
