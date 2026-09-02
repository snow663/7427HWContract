from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import sys

from .simulator import Simulator


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = Path(__file__).resolve().parent / "profiles" / "gm_16197427_31.json"


def number(text: str) -> int:
    return int(text, 0)


def dump(data: bytes, start: int) -> str:
    lines: list[str] = []
    for row in range(0, len(data), 16):
        chunk = data[row:row + 16]
        address = (start + row) & 0xFFFF
        hexes = " ".join(f"{value:02X}" for value in chunk)
        ascii_text = "".join(chr(value) if 32 <= value <= 126 else "." for value in chunk)
        lines.append(f"${address:04X}: {hexes:<47} {ascii_text}")
    return "\n".join(lines)


def print_result(sim: Simulator, result) -> None:
    detail = f" ({result.detail})" if result.detail else ""
    print(f"STOP={result.reason.value}{detail} INS={result.instructions} CYC={result.cycles} PC=${result.pc:04X}")
    print(sim.summary())


HELP = """Commands:
  step [n]                   execute n complete instructions (default 1)
  cycles <n>                 advance an E-clock budget; stop at instruction boundary
  run [n]                    run n instructions (default 100000)
  go                         run continuously in bounded batches; Ctrl-C stops
  break <addr>               toggle PC breakpoint
  obreak <addr>              toggle output-register breakpoint
  irq <name|vector>          request IRQ/XIRQ/TOC1..TOC5 or vector address
  set <input> <value>        set rpm/state/adc.0..adc.7/ports/trace metadata
  inputs                     show current input state
  peek <addr> [count]        inspect bytes
  poke <addr> <value>        write RAM/device byte; ROM writes are blocked
  patch <addr> <value>       deliberately patch one ROM byte
  watch <addr> [r|w|rw]      add bus watchpoint
  trace [n]                  show recent execution entries
  bus [n]                    show recent rich bus records
  outputs [n]                show recent command/output writes
  scenario <path>            load a cycle-scheduled JSON scenario
  save-trace <path>          write bus/output/event JSONL
  image                      show BIN identity and digest
  regs                       show CPU/mapping/counter state
  reset                      reset CPU/devices and scenario cursor
  help                       show this help
  quit                       exit
"""


def repl(sim: Simulator) -> None:
    print("GM 16197427 $31 contract ROM simulator")
    print("HAC symbols, when loaded, are shown as :hac_hint rather than contract facts.")
    print(HELP)
    while True:
        try:
            raw = input("romsim> ").strip()
        except EOFError:
            print()
            return
        except KeyboardInterrupt:
            print()
            continue
        if not raw:
            continue
        try:
            parts = shlex.split(raw)
            cmd = parts[0].lower()
            if cmd in {"quit", "exit", "q"}:
                return
            if cmd in {"help", "?"}:
                print(HELP)
            elif cmd in {"regs", "where"}:
                print(sim.summary())
            elif cmd == "image":
                print(sim.image_summary())
            elif cmd == "inputs":
                print(sim.inputs.summary())
            elif cmd == "set":
                sim.set_input(parts[1], parts[2])
                print(sim.inputs.summary())
            elif cmd == "step":
                count = number(parts[1]) if len(parts) > 1 else 1
                for _ in range(count):
                    sim.step_instruction()
                print(sim.summary())
            elif cmd == "cycles":
                print_result(sim, sim.run_cycles(number(parts[1])))
            elif cmd == "run":
                count = number(parts[1]) if len(parts) > 1 else 100_000
                print_result(sim, sim.run(max_instructions=count))
            elif cmd == "go":
                try:
                    while True:
                        result = sim.run(max_instructions=100_000)
                        if result.reason.value != "limit":
                            print_result(sim, result)
                            break
                except KeyboardInterrupt:
                    print()
                    print(sim.summary())
            elif cmd == "break":
                address = number(parts[1]) & 0xFFFF
                if address in sim.breakpoints:
                    sim.breakpoints.remove(address)
                    print(f"Removed breakpoint ${address:04X}")
                else:
                    sim.breakpoints.add(address)
                    print(f"Breakpoint ${address:04X}")
            elif cmd == "obreak":
                address = number(parts[1]) & 0xFFFF
                if address in sim.output_breakpoints:
                    sim.output_breakpoints.remove(address)
                    print(f"Removed output breakpoint ${address:04X}")
                else:
                    sim.output_breakpoints.add(address)
                    print(f"Output breakpoint ${address:04X}")
            elif cmd == "irq":
                sim.request_interrupt(parts[1])
                print(f"Queued interrupt {parts[1]}")
            elif cmd == "peek":
                address = number(parts[1])
                count = number(parts[2]) if len(parts) > 2 else 16
                print(dump(sim.peek(address, count), address))
            elif cmd in {"poke", "patch"}:
                address, value = number(parts[1]), number(parts[2])
                sim.poke(address, value, allow_rom=(cmd == "patch"))
                print(f"${address & 0xFFFF:04X} <- ${value & 0xFF:02X}")
            elif cmd == "watch":
                address = number(parts[1]) & 0xFFFF
                mode = parts[2].lower() if len(parts) > 2 else "rw"
                if "r" in mode:
                    sim.memory.add_watch_read(address)
                if "w" in mode:
                    sim.memory.add_watch_write(address)
                print(f"Watch ${address:04X} {mode}")
            elif cmd == "scenario":
                sim.load_scenario(parts[1])
                print(f"Loaded {parts[1]}")
            elif cmd == "save-trace":
                sim.trace.write_jsonl(parts[1])
                print(f"Wrote {parts[1]}")
            elif cmd == "trace":
                count = number(parts[1]) if len(parts) > 1 else 20
                for row in sim.cpu.exec_trace[-count:]:
                    pfx = f"{row.prefix:02X} " if row.prefix is not None else ""
                    label = sim.symbols.label(row.pc)
                    hint = f" [{label}:hac_hint]" if label else ""
                    print(f"CYC={row.cycle:9d} PC=${row.pc:04X}{hint} OP={pfx}{row.opcode:02X} {row.text}")
            elif cmd == "bus":
                count = number(parts[1]) if len(parts) > 1 else 20
                for row in sim.trace.accesses[-count:]:
                    symbol = f" {row.symbol}" if row.symbol else ""
                    print(f"CYC={row.cycle:9d} PC=${row.pc:04X} {row.access_type} ${row.address:04X}=${row.value:02X} {row.device}{symbol} [{row.evidence}]")
            elif cmd == "outputs":
                count = number(parts[1]) if len(parts) > 1 else 20
                for row in sim.trace.outputs[-count:]:
                    digits = 4 if row.width == 16 else 2
                    print(f"CYC={row.cycle:9d} PC=${row.pc:04X} ${row.address:04X}=${row.value:0{digits}X} {row.name} [{row.evidence}]")
            elif cmd == "reset":
                sim.reset()
                print(sim.summary())
            else:
                print(f"Unknown command {cmd!r}; type help")
        except (IndexError, ValueError, KeyError) as exc:
            print(f"Input error: {exc}")
        except Exception as exc:
            print(f"Simulator error: {exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Contract-driven GM 16197427 $31 ROM simulator")
    parser.add_argument("binfile", nargs="?", help="64K, 48K, or 32K BIN image")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE), help="PCM contract profile JSON")
    parser.add_argument("--base", type=number, help="explicit BIN load base")
    parser.add_argument("--hac-html", help="optional HAC HTML annotations (always tagged hac_hint)")
    parser.add_argument("--scenario", help="cycle-scheduled scenario JSON")
    parser.add_argument("--steps", type=int, default=0, help="run this many instructions before exit/REPL")
    parser.add_argument("--cycles", type=int, default=0, help="run this E-clock budget before exit/REPL")
    parser.add_argument("--trace-out", help="write JSONL trace at exit")
    parser.add_argument("--repl", action="store_true", help="enter the interactive operator console")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sim = Simulator.from_profile_file(args.profile)
    if args.binfile:
        sim.load_bin(args.binfile, args.base)
    if args.hac_html:
        count = sim.load_hac_symbols(args.hac_html)
        print(f"Loaded {count} HAC hint lines")
    if args.scenario:
        sim.load_scenario(args.scenario)
    if args.trace_out:
        sim.trace.start_stream(args.trace_out)
    if args.binfile:
        sim.reset()
        print(sim.image_summary())
        print(sim.summary())
    if args.steps:
        print_result(sim, sim.run(max_instructions=args.steps))
    if args.cycles:
        print_result(sim, sim.run_cycles(args.cycles))
    if args.repl or not args.steps and not args.cycles:
        repl(sim)
    sim.trace.close_stream()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
