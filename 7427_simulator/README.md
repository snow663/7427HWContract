# 7427 Firmware Simulator — Clean-Room Implementation (v0.1)

A **fresh** Python/Tkinter implementation for the GM 16197427 ($7427) HC11.
This is **not** an upgrade or fork of `hac31_romsim`. Both live separately
in the same Git repository. This new implementation uses the factory-ROM
hardware contract, not the legacy simulator source, as its authority.

## Clickable desktop startup

Requires Python 3.10+ with Tkinter (included in normal Windows Python).
On Windows, double-click **`Launch_7427_Simulator.cmd`** or
`Launch_7427_Simulator.pyw`. On Linux/macOS from this directory:

```sh
python3 -m sim7427
```

Click **Load BIN** (32/48/64 KiB). **Step** executes one implemented HC11
instruction, **Run** executes small batches without freezing the UI,
**Pause** and **Reset** control execution. CPU registers, breakpoints,
manual IRQ injection, memory editing and recent bus/output events are shown.
Debugger ROM patches modify only the in-memory simulated image, never the
file on disk.

## Architecture

- `sim7427/cpu.py` — small new MC68HC11 interpreter, CPU state, stack,
  reset, interrupt push/RTI restore. **Unsupported opcodes stop loudly.**
- `sim7427/bus.py` — 64 KiB CPU-visible address space, INIT=$03
  relocates CPU registers from $1000 to $3000, shadowed/working RAM,
  ROM writes rejected, independent bus transaction log.
- `sim7427/machine.py` — reproducible execution session, ROM SHA256,
  reset, run/step, breakpoints and watchable output accesses.
- `sim7427/gui.py` — clickable local engineering workbench.
- `tests/` — synthetic ROM tests for instructions, reset/INIT, ISA
  rejection, IRQ stack order/RTI and GUI import.

**Current ISA subset:** NOP, SEI/CLI, LDS/LDX/LDAA/LDAB/LDD immediates,
LDAA/STAA/STAB/STD/STX addressing forms used in reviewed bootstrap/IRQ
slices, CLR, BSET/BCLR, COMA, INX/DEX, CPX/CMPA, conditional branches,
JMP, JSR, RTS, TSX and RTI. This does **not** execute the complete stock
BMHM engine loop yet. Encountering other opcodes is a deliberate
`UnknownInstruction` stop, with PC and opcode.

## Authority and boundaries

The source contract establishes register relocation INIT=$03,
$0000..$03FF internal RAM, used working RAM including $0800..$08FF,
$3060+ board output windows, and program ROM $4000..$FFFF.
**The memory system models CPU-visible behavior, not the physical memory
device providing shadow RAM.** No time is spent proving a device that
is outside the firmware software contract.

The first milestone does not invent ADC-channel mappings, active engine
input wiring, ASIC side effects, cycle-accurate timing, full HC11 instruction
coverage, watchdog reset, timer compare scheduling, ALDL or C source
execution. Engine input fields are intentionally **not connected** until
their software-visible register mapping is source-backed. Output log entries
reflect bus commands, not proven physical pulse durations.

The native ASM11 gateway in `source/replacement_os/hal/native_isr_gate.asm`
and the C mailbox in `pseudo-source/platform/` are the next differential
simulation targets once the relevant HC11 instruction forms are implemented.

## Run automated tests

```sh
cd 7427_simulator
python3 -m unittest discover -s tests -v
```

No third-party Python dependencies. No firmware flashing, writes to truck
hardware, or changes to `main`.

## Next milestones

1. Complete HC11 opcode/addressing-mode matrix using the NXP M68HC11RM
   with per-opcode tests and explicit CPU timing evidence.
2. Implement timer flags, ADC, SCI/ALDL and chip-select-visible ASIC
   effects only where the factory hardware contract establishes them.
3. Exercise assembled safe bootstrap and the new native ISR gateway
   from ROM bytes; validate CCR, stack and RTI with differential traces.
4. Run identical input/event traces against native BIN and C pseudo-source
   model and report divergence, not silently normalize it.
