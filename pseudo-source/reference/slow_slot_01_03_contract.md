# Stock slow slots 01, 03 and 0B

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

## Slots 03 and 0B — `$7ABD` and `$7B3D`

Slot 03 reads `$0086.6`, calls the optional `$1806` module when enabled and
writes `$F7` to `$0F00` on continuation. A missing enabled module returns
`PCM_UNIMPLEMENTED`. A failed call or write stops that pass. Slot 0B enters
gear selection directly. Both slots then run `pcm_transmission_gear_select`
(`$D4EB`) followed by `pcm_transmission_outputs` (`$C514`) on the default
scheduler path.

`slow_slot_03_contracts` checks the optional call, marker, named-state handoff
and failure exits. `gear_slots_rom_differential` compares both complete
scheduled paths with the recorded BMHM image. All 602 resident instruction
starts were reached from the two entries. The optional module body and
physical outputs remain external validation work. [Detailed gear-selection ledger](transmission_d4eb_source_closure.md)

The next slow slot is **04**, followed by 05, 0A, 0C and 0D. [Source closure plan](source_closure_plan_2026-11-20.md)
