# True E-cycle core design

The current CPU commits a complete instruction atomically. The rest of the simulator was split into stable interfaces so the CPU can be upgraded to a micro-operation sequencer without rewriting the PCM bus, devices, scenarios, traces, or console.

## Required sequencer state

```text
instruction_start_pc
prefix/opcode
addressing-mode phase
effective address
operand latch
writeback latch
remaining E cycles
pending CCR updates
interrupt sample point
```

## Per-cycle contract

Each `tick_e()` call will perform exactly one of:

```text
opcode fetch
prefix fetch
operand fetch
effective-address formation
data read
ALU/internal cycle
data write
stack read/write
vector read
instruction commit
```

Every external access will carry its actual E-cycle, AS phase, R/W state, Port-B high address, Port-C multiplexed address/data, and interrupt context. Internal accesses will remain on the same logical trace but be marked non-external.

## Upgrade acceptance tests

1. `cycles 1` advances exactly one E cycle without early architectural writeback.
2. Instruction-boundary results match the current functional core for every opcode used by BMHM.
3. Reset and interrupt bus sequences match the MC68HC11 timing reference.
4. `$301C/$301E/$3020/$3022/$3023` event order matches a captured bench trace.
5. Expanded-bus address/data phases match logic-analyzer capture.
6. A full stock-BMHM scenario produces no trace-order regressions outside intentionally corrected timing.

