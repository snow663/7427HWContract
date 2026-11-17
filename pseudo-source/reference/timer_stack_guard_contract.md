# Timer stack guard: source-level policy at $7959–$7979

The active branch implements `pcm_timer_stack_guard(pcm, stack_x, &needs_reset)`
as the **resident decision and RAM-transaction portion** of the periodic OC3
stack guard. The stock BMHM listing gives:

```asm
7958 CLI
7959 TSX
795A PSHX
795B PULX
795C BRSET $004F,#$04,$7967
7960 CPX #$03F7
7963 BLS $796C
7965 BRA $7971
7967 CPX #$03EE
796A BHI $7971
796C CPX #$03B0
796F BCC $797A
7971 BSET $003A,#$08
7974 BCLR $004F,#$04
7977 LDS #$03F6
797A JSR $7B6D
```

The HC11 `TSX` observes **SP+1**, rather than a native C stack pointer.
The `PSHX/PULX` pair preserves the observed X value at the comparison.
This value must be captured by a target-specific entry shim. The tested
software policy is:

| Sampled `$004F.2` | Healthy captured X | Recovery otherwise |
|---|---|---|
| Clear (not busy) | `$03B0..$03F7` inclusive | Set `$003A.3`, clear `$004F.2`, then `LDS #$03F6` |
| Set (busy) | `$03B0..$03EE` inclusive | Same ordered recovery |

`$004F` is read once for the branch. Upon an invalid stack X,
`$003A` is freshly read and byte-RMW written with bit3 set; `$004F`
is **read again**, then written with bit2 clear. Both accesses go through
the established logical-address provider, which must bind `$003A.3`
to `PcmSystem.stack_recovery` and `$004F.2` to `PcmScheduler.busy`
while preserving other bits. A failed read/write stops immediately with
the already successful prefix retained.

The output `needs_reset=true` means the **software** portion succeeded and
the **target shim must still execute `LDS #$03F6`** before transfer to
`$797A`. The source does not reset the host C stack. Existing
`pcm_periodic_irq` intentionally retains `PcmPlatform.check_stack`
until an actual HC11 entry/frame/recovery ABI is available; it does not
silently substitute this helper as a target implementation.

A dedicated host fixture enumerates both busy states and all 65536 X values
(131072 threshold cases), the five transaction-failure prefixes, fresh-read
mutation and invalid/missing provider contracts. These are test definitions;
no new ROM differential run or full project suite is claimed by the source
addition alone. Future integration should compare actual ROM instruction
starts, preempting interrupts at the literal CLI and resumption after LDS,
and stacked CCR/PC/SP recovery with the target ABI.
