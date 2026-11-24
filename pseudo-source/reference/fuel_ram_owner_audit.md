# Scheduled fuel root: canonical RAM provider / alias audit

Stock authority: BMHM $7D4B..$7E4E and $852C..$8547 as checked against
the SHA-identified ROM evidence. C ownership authority:
`pseudo-source/include/pcm.h` on this branch.

## Current partial provider bridge and why activation is still withheld

The stock $7D4B ignition prelude uses literal logical RAM accesses through
`pcm_read8/16` and `pcm_write8/16`; most downstream C calculations
consume canonical named fields in `Pcm`. The explicit,
**opt-in** `PcmPlatform.bind_fuel_ram_owners` mode now resolves selected
fuel-prefix RAM addresses through `fuel_ram_owner_read8/write8/read16/write16`.
Every access still invokes the original physical-width provider transaction;
an I/O failure never publishes a subsequent canonical field change.
Shared flag bytes reconstruct only source-owned bits over the residual
provider byte, and split big-endian word bytes share the same named word.

This sparse bridge is host-tested through the real `pcm_read/write`
drivers, with the underlying raw test provider deliberately **not**
mirroring C state. It closes the tested alias split, but is not a complete
RAM/ASIC/target provider: unknown addresses continue using the raw backend,
and newly added C producers may need extra owners or a change-order review.
The default platform flag is **false**; historical suite behavior is intact.
After PR48 reconciliation, the default C-source `pcm_fuel_control` root
executes the separately validated PR48 resident implementation. The
independent closure `pcm_fuel_cycle()` remains an **opt-in alternative**:
only both `enable_resident_fuel_cycle` and `bind_fuel_ram_owners` enable
it. The default `bind_fuel_ram_owners` flag itself remains **false**.
Neither C entry proves the physical PCM RAM/ASIC/timing/target ABI.

## Address-to-owner handoff

| Logical RAM | Source action/consumer | Existing canonical C owner | Provider status |
|---|---|---|---|
| $027E..$027F | Read, increment, write ignition/cycle count at 7D4B/7DAD | `system.fuel_ignition_counter` (new) | Mapped; target provider pending |
| $0044.4 | Source ignition-qualified gate | `reference.latch_inhibited` (same bit, current naming) | Mapped to canonical bit; semantic review pending |
| $0004.7 | Restart clear | `spark.bypass_supervision` | Mapped by opt-in sparse adapter; full provider pending |
| $0004.1/.0 | Restart clear | `fuel.oxygen_warmed`, `fuel.oxygen_activity` | Mapped by opt-in sparse adapter; full provider pending |
| $0004.3 | Reset running transition | `spark.run_transition` | Mapped by opt-in sparse adapter; full provider pending |
| $0019.6/.5 | Clear faults | `reference.bank_fault`, `spark.est_fault` | Mapped by opt-in sparse adapter; full provider pending |
| $00FD..$00FE | Reset source run timer | `scheduler.run_counter` | Word mapped; target provider pending |
| $024C..$024D | Reset delivered sync command | `reference.delivered_pulse` | Word mapped; target provider pending |
| $0062 | Reset RPM coordinate | `reference.rpm_coordinate` | Mapped by opt-in sparse adapter; full provider pending |
| $02CD | Reset DRP count | `reference.crank_references` | Mapped by opt-in sparse adapter; full provider pending |
| $02CE | Reset event age | `reference.event_age` | Mapped by opt-in sparse adapter; full provider pending |
| $0268 | Reset enrichment age | `reference.enrichment_age` | Mapped by opt-in sparse adapter; full provider pending |
| $0051.3 | Restart/off history | `runtime.ignition_off` | Mapped by opt-in sparse adapter; full provider pending |
| $0086.3 | Ignition off/on latch | `system.retained_initialized` (bit3) | Mapped; target provider pending |
| $004F.7/.4 | Clear running spark/fuel | `runtime.spark_running`, `runtime.fuel_running` | Opt-in mapped, critical full-cycle test required |
| $0046.7 | Clear previous CL history | `fuel.closed_seen` | Mapped by opt-in sparse adapter; full provider pending |
| $0044.3 | Clear first-reference latch | `spark.first_reference` | Mapped by opt-in sparse adapter; full provider pending |
| $003E.3 | Clear startup context flag | `io.coolant_context` bit3 | Mapped with owned-bit mask |
| $0223 | Reset EGR diagnostic count | `io.egr_failure_count` (new) | Mapped; target provider pending |
| $027D | Reset cold P/N time | `fuel.startup_park_hold` | Mapped by opt-in sparse adapter; full provider pending |
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

The [joined-fuel development run](https://github.com/snow663/7427HWContract/actions/runs/44748475806)
passed **45 of 45 fast contracts**, including the opt-in RAM-owner
roundtrips and a connected `pcm_fuel_cycle` test. The joined fixture
traverses all eight phase values with authorization denied and an actual
zero-injector-word publication; it also tests an authorized/uninhibited
running fuel calculation, ignition trap before publication and early
provider-operation failures. The two independently replayed BMHM ROM
comparisons also pass: $8EB4..$9166 governor (optional $1809 excluded)
and $7D4B..$7DB5 ignition, which stops before emulator-unsupported
terminal opcode $CF at $7D8D.

That historical45-contract checkpoint did not establish complete-cycle ROM
equivalence. The later [joined fuel contract](fuel_cycle_joined_contract.md)
records3,096 selected full-entry/retained-history comparisons, and the
[reconciliation ledger](reconciliation_2026-11-22.md) records combined-tree
validation. PR48's resident controller is now the default; the independent
closure cycle requires both research flags. Exhaustive interrupt interleavings,
external machine modules and physical target binding remain separate work.
