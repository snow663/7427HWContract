# Connected scheduled fuel cycle host contract — $7D4B..$8547

The resident `pcm_fuel_cycle` composes the stock order of ignition/COP
precheck, MAP/TPS/O2 and density prelude, existing crank/running calculation
and pulse delivery, and the $852C phase-selected tail. The default `PCM_FUEL_CONTROL` fast-dispatch root still delegates to the
explicit task. A new `PcmPlatform.enable_resident_fuel_cycle` **research-only
opt-in**, guarded by `bind_fuel_ram_owners`, connects the actual
`pcm_fuel_control()` wrapper to the contiguous source cycle. Missing
RAM binding fails closed with `PCM_BAD_CONFIGURATION` before any bus
operation. The host test verifies the default/delegated, denied/missing
provider and admitted/successful paths. This does **not** authorize
hardware deployment or establish a flashable HC11 BIN.

## Grounded verification

`tests/fuel_cycle_joined_test.c` reuses the mature calibrated
`fuel_delivery_test.c` host fixture, but opts in to the new
`PcmPlatform.bind_fuel_ram_owners` mode and therefore tests the real
`pcm_read8/read16/write8/write16` logical API. Test-only bytes provide
ROM and device transactions. Both source-owned and unowned bits retain
one coherent view at the moment of read. The test **does not** create a
new production RAM mirror.

| Scenario | What is tested |
| --- | --- |
| All eight phase values 0..7, authorization pending | Ignition counter $027E increments, watchdog COP55, transient MAP + normalized TPS + O2 + density all complete; $7E4F gate denies fuel authorization and publishes exactly one zero injector word at $3FCE; phase-selected tail returns normally |
| Phase 2, authorized running, uninhibited latch | Full `pcm_fuel_construct` and `pcm_fuel_deliver` are traversed using stock-derived calibration model; synchronous/async output hardware transaction reaches the provider |
| Ignition elapsed at threshold | $7D4B prefix clears running state through canonical RAM aliases, updates terminal board $3039 and IRQ mask, returns `PCM_HALT_BOUNDARY` before fuel delivery; no injector write |
| Early bus failure at provider operations 1..4 | No later injector output or density publication; completed initial count writes are retained according to their exact failure position |

The [development fast gate](https://github.com/snow663/7427HWContract/actions/runs/44749213748)
passes **45/45 fast contracts** including the joined fixture, and passes
both independent **governor** and **ignition** BMHM C/ROM differential
suites. The latter stops at the deliberate $CF terminal instruction
boundary $7D8D after comparing prior stock effects.

## Open source/target verification

The new joined test is a **C host contract**, not a full
instruction-by-instruction independent HC11 replay of $7D4B..$8547.
It does not prove every ROM phase, governor option, calibration history,
BLM state, AE/PE path, async packet or interrupt-injected failure edge
across the whole call graph. The optional $1809 A/carry module still
requires an actual source-backed interface. Canonical RAM aliases are
implemented for selected inputs and prelude state but the full RAM,
peripheral and external ASIC map is not complete.

Before replacing `pcm_fuel_control`, compare complete source-driven
cycles and failure prefixes against the stock ROM, including nonzero
fuel delivery and all phase variants, then validate target timing and
ABI separately. Do not infer physical injector execution or a
flashable BIN from the host suite.
