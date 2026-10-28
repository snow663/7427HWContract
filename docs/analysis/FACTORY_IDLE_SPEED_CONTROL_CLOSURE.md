# Factory IAC, RPM/VSS and governor documentation closure

The resident IAC controller and output service, RPM/VSS calculations, electronic governor and their local speed/fault/limit interactions are documented from actual stock BMHM bytes. The IAC and governor worklist items can now be crossed off within this software scope. This extends [the completed engine-calculation chain](FACTORY_ENGINE_CALCULATION_CLOSURE.md); it does not declare transmission, all diagnostics/service paths or physical device behavior complete.

## Completed software scope

| Item | Completed content | Contract |
|---|---|---|
| IAC target RPM | Coolant/gear/AC curves, battery/rough-idle/BLM/startup additions, slew and switch correction, stall threshold | [IAC controller](FACTORY_IAC_CONTROLLER.md) |
| IAC airflow and step target | Qualification, integral/cold allocation, P/D, transition/stall/DFCO/follower terms, BARO/kicker scaling, interpolation to0008 and IAC-change fuel AE087F | [IAC controller](FACTORY_IAC_CONTROLLER.md) |
| Learned/retained state | Boot checksum/conditional clears, byte versus word seeds, snapshots, cold decay, gear/AC transfer preparation and commit | [Learning and output](FACTORY_IAC_LEARNING_AND_OUTPUT.md) |
| Follower, cracker and kicker | VSS-indexed lag/delay, minimum cracker, hot-start state, on/off timers, TPS-zero baselines and output request | Both IAC contracts |
| Reset and service | Position255/target0 reset, completion/park, VSS/key-off triggers, local diagnostic qualifications and nonlocal service exits | [Learning and output](FACTORY_IAC_LEARNING_AND_OUTPUT.md) |
| Phase and hardware command | Direction reversal, all four ring states, enable retention, count/phase distinction, output shadow, actual latch order, coalescing and shared writers | [Learning and output](FACTORY_IAC_LEARNING_AND_OUTPUT.md) |
| RPM inputs | Existing normal/alternate coordinates plus both REF writers of006A, ratio006C, derivative consumers and state age | [RPM/VSS/governor](FACTORY_RPM_VSS_GOVERNOR.md) |
| VSS production | Timestamp polling, observed-event count, fixed-point quotient, startup batch, timeout and separate filter | [RPM/VSS/governor](FACTORY_RPM_VSS_GOVERNOR.md) |
| Electronic governor | RPM/VSS modes, anticipation/recovery, target/lead/integral separation, actuator I/P, service/fault and shared306C output | [RPM/VSS/governor](FACTORY_RPM_VSS_GOVERNOR.md) |
| Separate speed-related fuel paths | Hard RPM/VSS cut thresholds/hysteresis/delay, raw-speed abuse qualification and governor-option fallback | [RPM/VSS/governor](FACTORY_RPM_VSS_GOVERNOR.md), with the completed fuel handoff |

The new contracts take precedence over the narrower source-only IAC notes where they left strategy/cadence/reset unresolved. Existing replacement-OS preservation requirements and physical bench questions retain their separate purpose.

## ROM authority and reproduction

Both supplied 65,536-byte BMHM images have SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`. CPU4000..FFFF maps to the same full-file offsets. File0000..3FFF is padding; it does not supply CPU low-memory RAM/extension implementations. The original HAC is retained, normalized source SHA `7d1f46cab692621f7713c0eed46396feb26dc6eebeced451dc700426f2d49e9c`.

| New artifact under `maps/structure/` | Meaning |
|---|---|
| `bmhm_idle_governor_rom_evidence.json` | Image/source identity and captured instruction/data/calibration bytes |
| `factory_idle_governor_blocks.csv` | 45 reviewed instruction spans with document ownership |
| `factory_idle_governor_roots.csv` | 25 local CFG roots, return sites, calls preserved as boundaries; no unresolved local decoder frontiers |
| `factory_idle_governor_instructions.csv` | 2,876 instruction starts and explicit memory/address-mode inventory |
| `factory_idle_governor_branches.csv` | 816 condition/target/fallthrough rows using actual ISA flag rules |
| `factory_idle_governor_calls.csv` | Resident callees, opaque1803/1809, conditional A407 nonlocal-return boundary |
| `factory_idle_governor_states.csv` | 100 selected states, widths, direct writer overlap, other listing candidates and initialization classes |
| `factory_idle_governor_iac_cells.csv` | The retained cell layout and conditional indexed-store aliases |
| `factory_idle_governor_listing_discrepancies.csv` | 17 differences in the covered source/ROM spans, including previously reviewed helper/A40B cases |
| `factory_rpm_vss_consumers.csv` | 39 direct listing-seeded raw/filtered VSS readers checked against ROM; 30 linked to documented calculation paths, 9 retained as separate peripheral/diagnostic scope |

The eight words at9C96 are explicitly pointer data. ROM also restores missing park-snapshot instructionsA0FA..A113, missing entry9CA6, a shifted A361/A363 decode and shortened/malformed branch operands. These corrections are authoritative in the new byte inventories. The global listing/partial-overlay inventories remain their existing scope; this pass does not silently claim that every inherited row has been corrected or all alternate entries excluded.

```bash
python tools/verify_factory_idle_governor.py --rom /path/to/BMHM.BIN
python tools/verify_factory_idle_governor.py --check-recorded
```

Full-image mode checks SHA before decoding. Recorded mode checks committed excerpts and regenerated inventories without claiming a fresh image read. Both verify table pointers, key opcode anchors, span boundaries, local CFG inclusion, state/call inventories and document presence. The explanatory equations/algorithms are human reductions of those instructions, not mechanically proved by generating the same CSV twice. Existing bounded execution evidence remains separately labeled; no new simulator feature is required for this documentation closure.

## Findings that change interpretation

- **Software position is not a sensor reading.** Normal ring steps change0007 at91E6, but initialization, reset and reconciliation can change it without a phase edge. Reset sets0007=255 and target0008=0; it does not zero both.
- **Step cadence differs from target/latch cadence.** The per-entry step service precedes phase advance and busy checking. Main target calculation is later and slower; busy reentry can change the shadow without an immediate hardware flush. Reset suppresses a step only when all old phase bits03 are set.
- **Low battery does not always clear enable.** The low-voltage hold retains the old enable bit; the high-voltage branch explicitly clears it. Both hold count/phases.
- **Service can exit the controller.** Several A407 paths discard their own return address, tail into a reset/target/kicker operation, and return to93D0's caller. Treating every call as an ordinary return executes software the factory bypasses.
- **Literal ROM operands matter.**9343 tests config4E8F against RAM0008 via `BITA $08`, not immediate bit3. Position conversion uses a special wrapped increasing-delta interpolator. These are recorded rather than silently repaired to a plausible intention.
- **Governor and limiter are distinct.**400F.0 selects more than one actuator feature; it also changes fuel-cut fallback. Target255 clears actuator integral after forming the current output candidate.306C has another normal TCC writer and factory-test owners.
- **RPM history has two REF updates.**7537 copies0068 during non-fuel-running handling;7790 copies or filters it on the running status-event route. Ratio006C therefore needs both update lifetimes.

## Execution context and remaining interfaces

Nominal TOC3 tick is 6.248474 ms with phase00..9F. Rates below are admission opportunities, not measured hardware frequencies:

| Operation | Admission |
|---|---|
| IAC count/phase service91A3 | Every nonfactory timer entry before main phase increment/busy check; not repeated by tail catch-up |
| Board latchF411 and VSS sample7BF5 | Ordinary common fast group through7BA7; can repeat in catch-up passes; skipped by special fast-group mode |
| Main IAC93D0 | Ordinary phase&3=3, every 4 ticks nominal |
| Desired RPM/background9E99 | Slot7, every 16 ticks nominal |
| Follower/slow IAC A2B0 and VSS filterD4DA | Slot9, every 16 ticks nominal; A2B0 additionally requires spark-running |
| VSS quotientD4A3 | Fuel tail with phase bit1 clear, every 4 ticks nominal |
| Governor target8EB4 | Fuel tail low3=3, every 8 ticks nominal |
| Governor actuator90D3 | Ordinary odd fuel call with400F.0, every 2 ticks nominal |
| RPM change028D | Even conversion whenphase&1F=04; sampled every 32 phases nominal |
| IAC one-second-like timer substeps | Full slot phases07/09 where the code tests high nibble zero; once 160 phases nominal |
| IAC slow error/reset checks | Slot9 only with phase bit5 clear; not a uniform every 32-tick interval over the160-phase cycle |

| Interface | What is documented | Separate scope |
|---|---|---|
| Period/ADC/ports/capture counters | Exact software samples/transforms, GPIO mirror inputs, VSS quotient and timeout | Electrical scaling, hardware atomicity/count meaning, all acquisition and interrupt behavior |
| Gear00A2, AC request when400F.2, other input fault flags | Local IAC/governor qualification and resulting branches | Full transmission/range, AC and central diagnostic state machines |
| TPS zero02F6 | IAC-kicker writes and their effect on the normalized TPS input | Other TPS zero-learning/acquisition writers; no blanket ownership claim |
| Air quantity0232, AFR/PE/BLM and normal RPM | Connected to the completed engine calculation contracts | Physical units and full interrupt/intertask operating validation |
| Shared004B/004C/3062/306C | Actual local masks, arithmetic, command ordering and identified co-writers | Complete transmission/factory-test behavior, physical pin assignment, direction, actuator response |
| Opaque1803/1809 | Exact call guards, ordering and carry/early-store boundary | Low-memory implementation absent from the mapped stock image |
| Service payloads | Local selectors, target/retard/input edits and stack escapes | Full serial framing, received-payload ownership and factory command lifecycle |
| Other speed consumers | Individual direct instruction evidence and scope classification | Transmission/TCC/shift estimator, AC, purge and remaining diagnostics in the consumer ledger |

The remaining factory work is now primarily the separate transmission, broader emissions, central diagnostics/service and whole-program structure/ownership scopes, plus the named hardware/extension interfaces. This bounded completion supplies no audited whole-ROM understanding percentage. The stock source/algorithm authority remains distinct from the truck's previously recorded 2.bin calibration; this task changes documentation/evidence, not the running tune or actuator control.
