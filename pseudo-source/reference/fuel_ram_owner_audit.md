# Scheduled fuel root: canonical RAM provider / alias audit

Stock authority: BMHM $7D4B..$7E4E and $852C..$8547 as checked against
the SHA-identified ROM evidence. C ownership authority:
`pseudo-source/include/pcm.h` on this branch.

## Why activation is still withheld

The new `pcm_fuel_ignition_precheck` reproduces BMHM memory operations
through `pcm_read8/read16/write8/write16`, while most already-ported
calculations use **named C state owners** in `Pcm`. The current
`PcmPlatform` declares that providers must bind non-serial RAM to
those named owners, but it supplies no complete concrete mapping.
A test-only 65536-byte provider satisfies a standalone source slice,
**not** the complete controller. Without a coherent address provider,
a clear of $004F.4 on the bus would not change
`pcm->runtime.fuel_running`, and `pcm_fuel_calculate` could
select the wrong path in the same scheduled cycle.

Therefore `pcm_fuel_control` must continue to call the explicit
`PCM_FUEL_CONTROL` dependency until the provider is proven.
This is a correctness and live-injector safety boundary.

## Address-to-owner handoff

| Logical RAM | Source action/consumer | Existing canonical C owner | Provider status |
|---|---|---|---|
| $027E..$027F | Read, increment, write ignition/cycle count at 7D4B/7DAD | `system.fuel_ignition_counter` (new) | Provider alias pending |
| $0044.4 | Source ignition-qualified gate | `reference.latch_inhibited` (same bit, current naming) | Must reconcile gate meaning |
| $0004.7 | Restart clear | `spark.bypass_supervision` | Alias needed |
| $0004.1/.0 | Restart clear | `fuel.oxygen_warmed`, `fuel.oxygen_activity` | Alias needed |
| $0004.3 | Reset running transition | `spark.run_transition` | Alias needed |
| $0019.6/.5 | Clear faults | `reference.bank_fault`, `spark.est_fault` | Alias needed |
| $00FD..$00FE | Reset source run timer | `scheduler.run_counter` | Word alias needed |
| $024C..$024D | Reset delivered sync command | `reference.delivered_pulse` | Word alias needed |
| $0062 | Reset RPM coordinate | `reference.rpm_coordinate` | Alias needed |
| $02CD | Reset DRP count | `reference.crank_references` | Alias needed |
| $02CE | Reset event age | `reference.event_age` | Alias needed |
| $0268 | Reset enrichment age | `reference.enrichment_age` | Alias needed |
| $0051.3 | Restart/off history | `runtime.ignition_off` | Alias needed |
| $0086.3 | Ignition off/on latch | `system.retained_initialized` (bit3) | Provider alias pending |
| $004F.7/.4 | Clear running spark/fuel | `runtime.spark_running`, `runtime.fuel_running` | Critical alias needed |
| $0046.7 | Clear previous CL history | `fuel.closed_seen` | Alias needed |
| $0044.3 | Clear first-reference latch | `spark.first_reference` | Alias needed |
| $003E.3 | Clear startup context flag | `io.coolant_context` bit3 | Masked alias needed |
| $0223 | Reset EGR diagnostic count | `io.egr_failure_count` (new) | Provider alias pending |
| $027D | Reset cold P/N time | `fuel.startup_park_hold` | Alias needed |
| $3039 | $08 before trap | Physical board register | Explicit device write |
| $303A | $55 COP continuation | `PCM_COPRST` device register | Explicit device write |
| $0041.4 | MAP transient AC context | `io.ac_mirror` | Already C-owned |
| $0089.5 | MAP context gear bit | `transmission.range_context` | Already C-owned |
| $0047.0/.7-.1 | MAP transient context | `io.map_transient`, `io.map_context` | Already C-owned |
| $0063/$0065 | RPM delta | `spark.rpm_high`, `io.map_previous_rpm` | Already C-owned |
| $01C5 | MAP transient countdown | `io.map_hold` | Already C-owned |
| $0050.7 | Idle qualification | `spark.idle_state` | Already C-owned |
| $01D9 | Normalized TPS | `reference.throttle` | Already C-owned |
| $01D2..$01D3 | Filtered oxygen | `fuel.oxygen_filtered` | Already C-owned |
| $01C6 | Filtered MAP | `spark.map_filtered` | Already C-owned |
| $0299/$0293/$0294/$0286 | Governor state | `transmission.governor_*` | Already C-owned |
| $306C..$306D | Governor PWM command | Physical board word | Explicit device write |

**Important:** presence of a C field is not proof that its mapping,
bit lifetime, width, or reset ownership matches the stock ROM.
All overlapping byte owners must be unified without masking unrelated
bits. Stock bit labels in HAC are informative but not conclusive;
e.g. $0044.4 is called an ignition qualifier in the HAC but its
existing C model name is `reference.latch_inhibited`.
That semantic discrepancy must be resolved from consumers/branches,
not silently renamed.

## Required integration tests before replacing PCM_FUEL_CONTROL

1. Read/write-through tests: raw logical read/write and a named C
   access must observe **one** value (including split word bytes and
   read-modify-write bit operations).
2. Failure-prefix tests: a failure at each bus operation must retain
   completed writes and not publish a following injector/EST output.
3. Phase histories: run $7D4B..$8547 with all $0002.1/.2
   selections, including oxygen/VSS, battery/governor and battery/AFR.
4. Crank/first-run/steady-run: compare source ROM, current fuel
   authorization, shift/gear context, AE/PE, async packet and final
   $3FCE publications over multiple events, not isolated entries.
5. Optional module: when $0086.6 is set, $1809 must be supplied with
   correct native A/carry and clobber semantics; it cannot silently
   default to no-op.
6. Target: preserve physical chip-select register semantics, ISR
   atomicity and external ASIC writes; C passing ROM tests alone
   does not authorize a BIN.

## Verified focused slices

The branch fast GitHub Actions gate confirms all 43 existing quick
contracts and two new ROM comparisons: the $8EB4..$9166 governor
controller (excluding $1809) and the $7D4B..$7DB5 ignition prelude,
where ROM execution stops at the deliberate illegal/terminal byte
$7D8D rather than executing the emulator-unsupported opcode $CF.
These are scoped tests; the joined full fuel cycle is **not** yet proven.
