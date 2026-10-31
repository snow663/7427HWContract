# Resident REF event implementation

The C entry now connects the existing 74EA..751B prefix to the resident
751B..77C6 body and its local arithmetic/output callees. Authority remains the
hash-identified stock BMHM instruction bytes. Calibration fields and C RAM
placement are ours; the address references below identify their source meaning.

## Routine ownership

| Routine | Source scope | Responsibility |
|---|---|---|
| `pcm_reference_prefix` | 74EA..751B | Factory admission, OC1 compare, board strobes and pending latch |
| `pcm_reference_event` | 751B..7535 | Optional ADC transaction and crank/running dispatch |
| `pcm_reference_crank` | 7535..764F | Strict reference skip gate, crank delivery and event-age policy |
| `pcm_crank_event_gain` | 7827..7859 | Cold/warm/hot/repeat gain selection and saturated doubling |
| `pcm_fuel_async` | 8548..858A | Optional short-packet shaping and ordered 3FF2/3FFC transactions |
| `pcm_reference_crank_timer` | 7594..7628 | Both alternate crank timer branches |
| `pcm_reference_decay` | 7650..7696 | Additional-enrichment decay on running REF events |
| `pcm_reference_run` | 7696..7765 | Split-packet and bank-selection state transitions |
| `pcm_reference_common` | 7765..77C6; F479 | Additional request, load filter and extra timer admission |
| `pcm_reference_timer_arm` | 77C7..7826 | Parameterized OC5/OC4 arm helpers |
| `pcm_reference_bank_guard` | 785A..7874 | Saturating observation count and diagnostic latch |
| `pcm_lookup16`, `pcm_gain_word` | F4C1; F550 | Rounded fixed-point lookup and gain arithmetic |

Each public routine owns one source file. Private support helpers stay with
their owner. There is no longer a `PCM_REFERENCE_BODY` task dependency.
The original [reset/REF prefix note](reset_ref_transactions.md) remains the
reference for reset transactions and early reset assembly boundaries.

## Preserved details

Crank reference qualification is strict: deliver only when the incremented
02CD is greater than the coolant lookup, not equal. An inhibited or rejected
crank event acknowledges its flag and exits before the later 02CE update. That
age wraps from FF to F0 and has a separate low-battery cap.

The event-gain calculation uses four tables. Running enrichment decay keeps
the original two-shift coordinate rule: only carry from the second shift forces
FF. Counts retain their individual wrap, saturation, hold and reset policies.

The optional timer paths preserve fresh timer reads and the original N-only
modular comparisons. They are not replaced by ordinary unsigned or signed
numeric comparisons. The two arm routines retain their PORTA tests, flag writes,
TMSK1 read/modify/writes and conditional TCTL1/compare updates. A/B are logical
source channels, not independently verified injector-pin identities.

The asynchronous output writes its shaped packet plus the additive offset to
3FF2 even when the shaped value is zero. It reads 3FFC once, writes that sample
with 0400 clear, then writes the same sample with 0400 set. The driver does not
change the interrupt mask; the REF caller inherits the masked-entry contract.

The common tail consumes 0073.6 before its request gate. It retains F479's
intermediate 006A store followed by the returned filter result. The later extra
request and split-packet latches remain separate state fields.

In stock BMHM, 400B=04 and 400C=B7 select REF-triggered asynchronous crank output;
the optional OC4/5 event branches remain inactive. The C supports those resident
configuration branches as well, without claiming they are active stock paths.

## ADC and physical backend boundary

The MAP sample writes 3030=5, retains the nominal 33-E-cycle gap represented by
ASLD and three MUL instructions, and reads 3031. A required `delay_cycles` binding
provides at least that requested delay. Missing support returns
`PCM_NO_HARDWARE` after the ADCTL write and before the sample; it does not pretend
conversion completed. Target call overhead, actual ADC completion, clock/waits
and ISR deadlines still require the target compiler/backend and measurements.
The C does not add an ADC polling read that was absent from the source.

All read/write widths and ordered accesses remain explicit. The host callbacks
supply chosen peripheral responses and a timer sample sequence. Their success
is not proof of ASIC packet acceptance, physical output polarity or delivery.
An I/O failure returns at its current prefix, preserving prior state and
transactions. It does not synthesize a hardware rollback or safe-state action.
Target reset/interrupt assembly, ABI, real stack behavior and driver backend
remain unfinished. The source does not yet produce a target BIN.

## Differential verification

`tests/compare_reference_event_rom.py` executes the actual complete resident REF
interrupt, including its real CPU entry/RTI and callees, and compares compiled C:

- 2,502 full-handler cases cover stock calibration, explicit calibration variants,
  boundary counters, gain choices, packet limits, timer wrap, both timer channels,
  separate pending/latch fields, asynchronous shaping, ADC samples and factory exit.
- 143 injected I/O failures compare state and the successful transaction prefix.
- 38 direct crank-timer-entry cases cover driver inputs beyond the normal caller's
  pulse limit, including two otherwise unreachable overflow guards.
- 293 compiled calibration bytes match the stock ROM, using explicit byte order.
- All 423 scoped instruction starts are exercised across the full-handler and
  direct-driver cases. This is instruction coverage, not all-state equivalence.

The complete-handler cases cover 421 of those starts. 75B9 cannot overflow because
its multiply receives a word at most 7FFF and an unsigned byte gain. 760D cannot
overflow because its branch doubles the caller-limited word directly. The driver
entry tests supply larger words to exercise both defensive saturations. The
coverage distinction is asserted in the test, rather than hidden by an invalid
full-handler fixture.

The fixture explicitly models CPU timer flags as write-one-clear and supplies
per-read timer values. It does not generate physical timer edges. Only the RAM
bytes used by the real ROM CPU/call stack are excluded from the state comparison;
all other 0000..08FF bytes, the peripheral image and ordered I/O/delay requests are
compared. The C remains free to allocate its named state differently on target.

The prior 4,240 startup/prefix comparisons, 64 startup/prefix failure checks,
532 base-fuel comparisons and five kernel groups remain in both verification
routes. The C inventory is 109 public routines: 45 implemented outlines,
39 dependency boundaries and twenty-five implemented algorithms. These counts are
not a whole-firmware completion percentage.
