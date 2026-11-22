# M2 slow-slot closure: slot 01 complete, slot 03 started

Source of truth is the verified stock BMHM ROM, decoded HC11 instructions
and SHA-identified recorded ROM bytes. These modules are C pseudo-source,
not a flashable native HC11 target or an assertion of solenoid operation.

## Slot 01 — $7AAD..$7AB6 (source composition complete)

| Factory JSR | Resident source function | Source behavior |
|---|---|---|
| $7AAD -> $C583 | `pcm_baro_input` | BARO sensing, fallback/filter and derived AE/PE/load coordinates |
| $7AB0 -> $C668 | `pcm_speed_source` | source-selection priority for two calibrated speed words, or BARO-based rounded lag via stock $F436 |
| $7AB3 -> $ADAA | `pcm_tcc_non_electronic` | manual/non-electronic TCC option, MPH/TPS/coolant/RPM admission, two $F4C1 lookup paths, lock bit $0089.5, delay $0853 and TPS retention $0854 |

The new $C668 source differential is `speed_source_rom_differential`
(directed selector and randomized source/calibration histories).
The $ADAA body is checked by
`tcc_non_electronic_rom_differential` including its option-off,
lock/unlock, MPH, TPS, temperature and delay gates, and interpolation
endpoints. The combined wrapper is checked by
`slow_slot_01_contracts`, including the independently compiled PR48
default and the guarded closure alternative, with failure-prefix short circuits.

**Important:** The factory's `$ADAA` path updates **logical request
state** at $0089.5 and does not by itself prove physical TCC output.
Its eventual electrical output, any asynchronous interrupts and
automatic-transmission hardware remain target contracts.

`pcm_slot_01` is now a **resident source wrapper with two verified
implementations**. PR48's C583→`pcm_transmission_baro`→
`pcm_tcc_nonelectronic` remains the default after reconciliation.
With `PcmPlatform.enable_resident_slow_slots=true`, the alternative
C583→`pcm_speed_source`→`pcm_tcc_non_electronic` executes instead.
Neither variant's host success proves the physical TCC output.

## Slot 03 — $7ABD..$7AC6 (in progress)

Factory order:
1. $F5CF: on $0086.6, execute optional external module $1806;
   then publish literal decimal247 ($F7) to logical RAM $0F00
2. $D4EB: transmission/gear computation with substantial transitive
   $E684, $E6AC, $E69C and $D7xx/$D8xx helper graph
3. $C514: existing resident transmission output controller

The guarded `pcm_slot_03` now executes the literal $0086 flag
read, optional $1806 address callback, and $F7 -> $0F00 write.
It requires a real `call_address` boundary for $D4EB and does
not skip it; only a successful return permits the $C514 output
routine. Missing callback yields `PCM_UNIMPLEMENTED`, while
a failed callback or failed logical write stops immediately.
`slow_slot_03_contracts` checks these paths. This slot is still
an indexed `dependency_boundary`, not closed.

**Update, Nov 22:** source-backed $D4EB–$D4F7 diagnostics,
$D5B7–$D69E gear finalizer, $E562 and $D8CE now pass independent
ROM differentials; the middle $D4F7–$D5B6 and its other callees
remain outstanding. See [detailed D4EB ledger](transmission_d4eb_source_closure.md).

**Next:** close $D4F7–$D5B6 and remaining helpers without invoking
the stock $D4EB callback after a partial C prefix.
The optional module $1806 remains external and cannot be replaced
by arbitrary success.

## Verified development gate

[GitHub Actions run 44820137699](https://github.com/snow663/7427HWContract/actions/runs/44820137699)
passed the quick source contracts and five focused ROM-differential
suites covering the previous full fuel cycle, governor, ignition,
$C668 speed and $ADAA TCC. Remaining slow slots 04/05/0A/0B/0C/0D/0F
and the full $D4EB component are not claimed completed.

M1 source-level scope is recorded in
[source closure plan](source_closure_plan_2026-11-20.md).
All new work is retained on `work/pseudo-source-closure`.
No PR, release merge, or target BIN has been requested or performed.
