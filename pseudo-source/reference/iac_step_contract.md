# Resident IAC software count, phase and enable service

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
`pcm_iac_step` implements all48 instruction starts at91A3..920D. Its old
`PCM_IAC_STEP` task ID remains reserved and unused. No public routine is added;
the inventory is172 routines:76 implemented outlines,39 dependency boundaries
and57 implemented algorithms.

## State and admission

| Stock location | C owner | Meaning in this routine |
|---|---|---|
| 000A | `iac.step_control` | Direction01, ring0C, enable10; all other bits retained |
| 0007 /0008 | Existing `iac.position` /`iac.target` | Software count and requested count |
| 0009.0 | Existing `iac.state_flags` | Reset admission gate |
| 0002 | Existing `scheduler.phase` | Old phase byte, read before phase advance |
| 003E.2 | Existing `iac.low_battery` | Voltage-admission result |
| 0044.4 | Existing `reference.latch_inhibited` | Independent ignition/reset gate |
| 00A7 | Existing `spark.battery_sample` | Raw battery byte, not0055 |
| 004C | Existing `transmission.output_shadow` | Shared board output shadow |
| 4EB6 | `iac.step_battery_minimum` | Stock69 hex; strict greater-than admission |

Battery above169 clears enable and sets low-battery while retaining count/ring.
At/below169,0044.4 admits movement independently of4EB6. Otherwise battery must
be strictly greater than4EB6. A failed low-voltage admission sets low-battery but
retains the previous enable bit. This routine does not infer voltage scaling.

The profile is required only on the path that reads4EB6. A missing profile there
returns BAD_CONFIGURATION before any state write. The high-voltage and0044.4
bypass paths need no profile; they still require the later mask backend.

## Count and ring

An admitted equal count/target clears direction and retains the ring. Otherwise
reset suppresses movement only when **both** old phase bits03 are set. It also
suppresses a direction change on that call. Normal movement has no phase gate.

For unequal counts, set direction0 for increasing and1 for decreasing. Compare
that direction with the previous000A direction. Reversal updates the direction
without changing count or ring. A matching direction changes the count by1 and
advances the ring:

| Direction | Ring sequence |
|---|---|
| Increasing | 00 →04 →0C →08 →00 |
| Decreasing | 00 →08 →0C →04 →00 |

The both-set BRSET and neither-set BRCLR tests retain their actual meanings.
Direction/ring logic rereads volatile000A where the stock routine does; the
working command remains a separate local value corresponding to register B.
The software count is not a position sensor. Main-IAC reconciliation and reset
can change it without a ring edge; those owners remain separate.

## Commit order, masks and shared writers

1. Commit000A, after any count and low-battery changes.
2. Assign the IRQ mask true through `pcm_mask_irq` (literal SEI).
3. Read the current004C shadow and store `(old& E3)+(latched_command&1C)`.
4. Assign the IRQ mask false (literal CLI), even if entry was masked.

A failed first assignment retains the earlier count/control/voltage prefix and
leaves the shadow untouched. A failed final assignment retains the merged
shadow and the successful masked state. A missing mask binding has the same
completed-prefix behavior at its first use. These are C backend failure
contracts; a physical HC11 SEI/CLI is not claimed to fail.

Selected mask callbacks change000A and004C at the SEI boundary. The merge reads
the new shadow while retaining the command already held in B. CLI callbacks can
change state after the merge. Those fixtures establish the ordering, not a new
machine ABI or all possible interrupt interleavings. Target entry and coherent
access still need their own validation.

The routine writes no hardware latch. Existing C514 gear/current code shares
004C, and its raw gear-index addition can include neighboring data/code values.
Both sequential call orders are compared across all256 raw indices. This does
not make the unmasked gear writer commute with an interrupting IAC update.
The already documented preemption limit in
[the shared-output contract](../../docs/analysis/FACTORY_STACK_AND_SHARED_OUTPUT_CONTRACT.md)
remains in force. Common board I/O must still consume the shadow and sample the
input mirror; no physical phase polarity, direction or step rate is established.

## Scheduling and verification

Fast service calls the real step routine before ADC/current dependencies and the
busy test. Busy reentry therefore updates the count/shadow. Catch-up dispatch
repeats main work without another fast-service step. Both main-IAC and step task
bindings are absent from the kernel regression.

A busy-entry160-phase fixture supplies each old phase once with no intervening
main-controller target changes. It observes160 normal count updates or120 reset
updates. A separate injected-busy fixture observes four count advances across
one owner plus three busy entries, with only two common-I/O admissions. Their
observed shadows are14 then10 hex; the catch-up pass adds no step. These are
software admission/observation counts, not measured latch edges or motor rates.

The new corpus passes376,456 compiled-C/ROM comparisons:

- 131,072 position/target cases covering every byte pair with both old directions.
- 131,072 battery/threshold cases covering every byte pair and both0044.4 states.
- 65,536 old-control/shared-shadow byte pairs with interleaved count relations.
- 16,384 phase/control/reset cases, including every full phase byte.
- 7,680 callback/mask witnesses and15,360 failed SEI/CLI prefixes.
- 3,584 sequential shared-writer calls,2,048 joined controller cases and638 joined
 failure prefixes, plus1,024 retained histories,2,048 profile/state variants
 and10 direct/sequential/sixteen-entry cases.

Every scoped instruction start executes. The test rejects unexpected non-stack
RAM writes, checks completed ROM frame balance and compares mapped state, final
mask and ordered transactions/dependencies. The new source byte matches stock;
the inherited profiles/backings keep their existing stock checks. The full
CMake route now has36 entries, and the kernel has six contract groups.

Next connect common board I/O and input housekeeping while retaining their
remaining MAP/VSS/acquisition dependencies. Reset/interrupt assembly, the target
ABI, RAM/linker/stack fit, actual latch/backend behavior and physical motor
timing remain separate work. This is a host C implementation, not a target BIN.
