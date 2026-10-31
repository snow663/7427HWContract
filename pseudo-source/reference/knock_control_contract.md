# Scheduled knock work and normal spark consumption

Authority is the recorded stock BMHM image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The routines preserve raw byte/word arithmetic. Observation counts, the stored
retard byte and spark-command counts are different representations; these
checks do not establish sensor scaling or physical spark degrees.

## Routine ownership

| C routine | Stock instructions | Responsibility |
|---|---|---|
| `pcm_slot_08` | 7B2B..7B2E | Call decay, then the diagnostic; no remaining slot8 task boundary |
| `pcm_knock_decay` | CEBB..CEDA; F4C1..F4DD | Phase gate, interpolated rate, rounded decrement and zero floor |
| `pcm_knock_sensor` | CEDB..CF15 | Diagnostic enable, acquisition, fault counter and fault flag |
| `pcm_adc_mux` | F275..F27F, X=3000 | Clear PORTD bits38, then select with a fresh PORTD read |
| `pcm_adc_convert` | F25F..F274, X=3000 | Control write, at most12 ready polls, timeout flags |
| `pcm_knock_retard` | AA81..AADB | Atomic observation consumption and normal-KR command subtraction |

Each public routine has its own source file. The broad A466 spark root still
returns through its explicit dependency binding. Its future implementation must
call `pcm_knock_retard` at the AA81 position after the burst routine. Extracting
this callable slice does not complete the spark root or its physical output.

## State and calibration

| Factory location | Named C field | Meaning in this scope |
|---|---|---|
| 0203,020D | `knock.sample_baseline`, `knock.observation_accumulator` | Existing OC1 producer state |
| 020C | `knock.retard` | Byte state; subtraction uses its unsigned half |
| 0207,0019.4 | `knock.sensor_fault_count`, `knock.sensor_fault` | Sensor qualification history and live fault |
| 006E.1 | `knock.burst_active` | Explicit input from the unported burst logic |
| 0843,0844 | `knock.event_gain`, `knock.retard_limit` | Explicit inputs from the unported scheduled spark-gain producer |
| 0016 | `runtime.primary_faults` | Normal KR tests mask60 only |
| 001A.1,003A.0 | `runtime.adc_timeout`, `runtime.adc_fault` | Per-conversion timeout flag and retained timeout notification |
| 0002,0062,0006 | Existing phase, RPM coordinate and coolant fields | Shared inputs, not new duplicate state |
| 0063,0284 | `spark.rpm_high`, `spark.vehicle_speed_high` | High-byte consumers only; the full filtered-word producers remain separate |
| 01EE | `spark.command` | Wrapped word entering and leaving this spark slice |
| 45A5..45B5 | `calibration.knock.decay_rate[17]` | Rounded16-segment lookup |
| 45D8..45DA | `minimum_speed`, `minimum_rpm_high`, `minimum_coolant` | Raw admission thresholds |
| 4E74..4E77 | `sensor_fault_delay`, `sensor_upper`, `sensor_lower`, `fault_retard` | Diagnostic thresholds and fixed fault retard |
| 5B03.4 | Existing `calibration.reference.diagnostic_options` | Shared diagnostic enable byte, kept in one field |

New named state is initialized by the reset outline. That does not implement
the remaining factory reset stages or retained-state alternatives. Calibration
struct layout is still a source interface, not an EEPROM serialization format.

## Decay and sensor acquisition

Only a clear phase bit4 permits decay. On actual slot8 admissions in the
160-phase dispatcher, this means five decays and ten diagnostic opportunities
per complete phase cycle. A set bit skips decay and still runs the diagnostic.

The rate is `pcm_lookup16(RPM62,decay_rate)`. Multiply it by the old020C byte,
round by128 before taking the high byte, and use at least1 as the decrement.
Subtract from a fresh020C read with a zero floor. The diagnostic can run with
the resulting retard already committed; an acquisition failure does not undo it.

When5B03.4 is clear, retain sensor count, sensor fault, ADC flags, ports and mask.
When enabled, the exact acquisition sequence is:

1. Read PORTD3008; write it with bits38 clear.
2. Read PORTD3008 again; write that fresh value OR the byte-shifted selector0.
3. Assign the IRQ mask set, matching SEI.
4. Clear001A.1, write ADCTL3030=01, then read ADCTL at most12 times until bit80.
5. If none of those12 reads reports ready, set003A.0 and001A.1 and return normally
   from the conversion helper. A ready conversion leaves003A.0 retained.
6. Assign the IRQ mask clear, matching CLI, then read ADR4 at3034.

Thus the source selects **external mux0**, writes ADC control01 and consumes
ADR4. Calling this an on-chip ADC channel0 read would conceal the actual path.
No extra polling, sample suppression or software delay is inserted on timeout.

Samples in inclusive `[sensor_lower,sensor_upper]` clear count and sensor fault.
For an out-of-range sample, an old count greater than the delay sets the fault
without incrementing. Otherwise increment the byte and retain the old fault.
The comparison is strictly greater, and increment can wrap when delay=255.
Inverted lower/upper calibration bounds admit no valid sample.

## Normal KR consumer

AA81 performs literal SEI, reads020D, clears020D, then executes CLI before any
other admission test. An entry mask that was already set still leaves clear.
`volatile` alone is not a replacement for this critical section or a target ABI.

| Route, in order | Stored020C | Command change |
|---|---|---|
| Burst active, or0016 mask60 clear and coolant below45DA | Zero | Subtract zero |
| Otherwise speed below45D8 **and** RPM high below45D9 | Retain old byte | Retain command; no old retard subtraction |
| Otherwise sensor fault set | Fixed4E77, bypassing0844 cap | Subtract fixed byte>>1 |
| Otherwise | Saturating event increment plus old byte, capped at0844 | Subtract resulting byte>>1 |

On the normal update route, double the unsigned16-bit product of0843 and the
consumed observations. An ASLD carry forces candidate255 without reading old020C.
Otherwise add the high doubled-product byte to old020C and saturate at255.
Then cap at0844. The retained product fraction is discarded, not rounded.

Command subtraction wraps at16 bits. The byte saved on the factory CPU stack
at AACF..AADB becomes a local C subtraction value; the source does not alias a
native C frame to factory RAM. Burst arm/decay, low-octane learning, gain/cap
production, prior composite spark, subsequent signed limits, service edits and
period/EST conversion remain separate unfinished spark work.

## Failures and interrupt witnesses

Missing calibration returns `PCM_BAD_CONFIGURATION` before state or I/O work.
Missing callbacks and callback errors return at the current successful prefix.
A disabled diagnostic and pure decay need no hardware binding. Sensor failure
after SEI can leave the mask set. Failure at CLI occurs after any ADC timeout
flags; failure at the final sample occurs with the mask clear. A failed consumer
SEI retains020D; a failed CLI leaves020D cleared and the mask set. No rollback
or additional unmask operation is inferred.

Selected ROM/C witnesses place OC1 before SEI, attempt it while masked, and
place it immediately after the logical CLI boundary. The post-clear observation
remains pending while the consumer uses its previously captured byte. The ROM
side uses real interrupt entry and RTI and checks its saved register/frame state.
These are specified instruction-boundary fixtures, not a model of CLI recognition
delay, hardware pending-request delivery, physical timer edges or all interleavings.

## Verification

`tests/compare_knock_rom.py` compares compiled C with actual stock instructions:

- 131,584 decay cases: every stock RPM/retard pair, every constant rate/retard
  pair, all phase bytes and an ascending calibration curve.
- 139,502 normal-KR cases: every gain/observation pair, every old-retard/cap pair,
  command borrow/wrap witnesses, admission/fault combinations and calibration
  threshold boundaries.
- 6,394 sensor/slot cases, including threshold equality, inclusive endpoints,
  counter wrap, diagnostic disable, twelve-poll completion and timeout.
- 1,928 direct mux/ADC cases, including changing PORTD between its two reads,
  all selector bytes and control/readiness variants.
- 469 injected I/O/mask failure prefixes, 1,280 OC1→consumer→slot→consumer
  sequences, 1,536 logical mask-boundary IRQ witnesses and 330 history/recovery
  calls with diagnostic disable/reenable and a valid recovery sample.
- All 121 scoped instruction starts execute. All 153 supplied calibration bytes
  match stock: 24 new bytes, the existing shared5B03 byte and128 prior OC1 bytes.

The kernel regression also confirms ten real slot8 ADC starts per160 phases.
Both local verification routes retain every earlier kernel, fuel, reset, REF
and OC1 check and add knock contracts and this differential suite. This brings
the C inventory to 84 routines: 39 implemented outlines, 39 explicit dependency
boundaries and six algorithms. Counts and tested numeric domains do not prove
whole-firmware equivalence, target memory fit, stack bounds or physical timing.

See the [OC1 contract](oc1_knock_contract.md),
[upstream spark derivation](../../docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md),
[stack proof](../../docs/analysis/FACTORY_SPARK_INTEGER_HANDOFF.md) and
[physical interface boundaries](../../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md).
