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
`$797A`. The source does not reset the host C stack. `pcm_periodic_irq`
now optionally calls the helper when an entry shim supplies the sampled X
through `PcmPlatform.capture_timer_stack_x`; with that callback absent,
its prior `PcmPlatform.check_stack` boundary remains available to older
host fixtures. A valid captured X proceeds directly into
`pcm_periodic_irq_resume` at the $797A continuation. An invalid captured X
returns appended `PCM_STACK_RECOVERY_BOUNDARY` once the RMWs complete.
The target must then establish SP=$03F6 and transfer to that continuation.
The C status boundary is **not** a hardware stack reset or return from a
damaged native C call frame. Real target entry/RTI and interrupt nesting
remain explicitly unimplemented.

The kernel fixture joins guard capture, recovery status and a single $797A
continuation without rearming the timer. Its captured-X provider now commits
$004F.2, $003A.3 and $003A.5 to their canonical native owners; the fixture no
longer manually clears busy to make the continuation work. Both exact healthy
upper bounds and capture failure are checked. Supply of a valid SP after the
recovery boundary remains a target/test precondition, not a host stack reset.

Focused validation on 2026-11-22 passes **6,056 C/ROM comparisons** across
**all10 software instruction starts** at795C..7976. The comparisons execute
actual recorded BMHM bytes and independently observe each read/write, cause
preservation, captured/fresh busy reads, provider mutation and every access
failure prefix. Their event lists include the attempted failed transaction;
RAM state retains only the successful writes. Source X and SP remain unchanged
up to the explicit LDS boundary.

The existing host contract also ran and passed its **131,072 threshold cases**
(two busy states by all65,536 X values), plus failure/null/mutation checks.
Kernel and hardware smoke contracts pass. The default new ROM test includes
an exhaustive X sweep for the eventual release run; development used its
`--focused` boundary and byte-class selection. The full branch suite remains
deferred until "pull and merge". TSX/PSHX/PULX, native target recovery, interrupt
arbitration, stacked CCR/PC/SP and RTI are separate target ABI work.
