# Crank admission, startup/AE and commanded AFR/PE

This batch adds22 public routines. The source now has220 routines:106 implemented
outlines,83 implemented algorithms and31 dependency boundaries. Each public
routine owns one source file. These are callable slices of the recorded BMHM
image, not a target image or a completed scheduled fuel controller.

## Entries and stops

| Stock scope | C entry | Contract |
| --- | --- | --- |
| AE5C..AE84 | `pcm_fuel_authorize` | Capture-delta permission latch |
| 7E09..7E35 | `pcm_fuel_oxygen_filter` | Idle/coordinate gain and ordered O2 thresholds |
| 858B..85B1 | `pcm_fuel_crank_coordinate` | Captured-period scaling and FDIV coordinate |
| 85B2..8612 | `pcm_fuel_crank_pulse` | Coolant/age/BARO/TPS crank equation |
| 7E53..7EA5,84F5..852B | `pcm_fuel_crank_prepare` | History seeds, battery correction and conditional publication |
| 7E4F..7EB1 | `pcm_fuel_admit` | Crank or running authorization; returns whether AE/VE is next |
| 7EB2..7F20 | `pcm_fuel_map_acceleration` | MAP delta, entry threshold and enrichment amount |
| 7F21..7F85 | `pcm_fuel_tps_acceleration` | TPS hysteresis, speed/BARO gains and phase-bit history |
| 7EB2..7F85 | `pcm_fuel_acceleration` | Contiguous MAP/TPS body |
| E30B..E33B | `pcm_fuel_transient_gains` | Base, TPS and MAP transient gains |
| 8DEF..8E1C | `pcm_fuel_decel_history` | Counted TPS/MAP history update |
| E340..E38E | `pcm_fuel_startup_seed` | Nonrunning startup seeds and retained REF decrement |
| E38F..E3BA | `pcm_fuel_startup_context` | Literal SEI/CLI and low003F context |
| E3BB..E43B | `pcm_fuel_startup_afr` | Hold, park delay, interval and truncated AFR decay |
| E43C..E476 | `pcm_fuel_startup_spark` | Phase-window delay and truncated spark decay |
| E33C..E476 | `pcm_fuel_startup` | Nonrunning seed or running context/decays |
| 891E..899A | `pcm_fuel_afr_base` | Closed/open selection, startup subtraction and departure filter |
| 899B..8A21 | `pcm_fuel_afr_idle` | Idle readiness/timing, selected A-register AFR output |
| 8A22..8A8A | `pcm_fuel_afr_bias` | Hot/warm biases, upper cap, then REF-counted enrichment |
| 8A92..8C37 | `pcm_fuel_pe` | Permission, full/gradual gain, target and exit histories |
| 8C38..8C72 | `pcm_fuel_afr_finish` | Prior TPS, rich cap, service/extension and024B publication |
| 891E..8C72 | `pcm_fuel_afr` | Contiguous AFR controller, stopping before BLM8C73 |

`pcm_fuel_crank_prepare` requires the caller to have selected nonrunning mode.
`pcm_fuel_admit` performs that selection and reports false for the common852C
tail, or true for admitted running AE/VE. An unauthorized running call publishes
zero through the existing84F5 publisher; it does not run AE/VE. Ignition handling
at7D4B, preceding TPS/O2/density work and the common tail remain separate.

## State and arithmetic

Existing coolant, TPS, RPM, BARO, air-rate0232, idle state, runtime, startup spark,
PE gain0278 and REF enrichment02C9/0267/0268 owners are reused. Newly named state
covers authorization0851/003D.1, MAP/TPS histories01C7/01DC, AE flags/amounts,
startup02C8/02CA/02CC/0270/027D/0200, AFR0264/0266/0271/082C and PE timers.
003F low context is separate from existing upper-bit owners; rebuilding its low
nibble preserves the live extra-guard, PE-full, IAC-cancel and short-PW bits.
The shared003E context retains its existing owner and independently owned IAC bit.

Authorization uses wrapped TIC2 subtraction. A zero delta retains the baseline;
a nonzero delta saves it before inclusive lower/upper checks. The latch has no
local clear. The ordinary400D.6-clear path needs no hardware read.

The crank coordinate uses the low byte of32*4141 and returns zero for a zero
scaled period. FDIV overflow/equality saturates before the127 cap. Crank pulse
uses separate word gains; overflow in the first doubling skips TPS entirely.
Main crank preparation doubles again, refreshes battery0055 and stores the
battery-corrected02CF. Its delivery comparison is >=, unlike REF's strict >.
Option400C.2 leaves delivery to REF. Both main paths stop before852C.

MAP AE rounds its word delta, applies idle/closed-throttle thresholds, and uses
truncated doubled and /32 products. TPS AE uses the old fractional history to
round the positive difference, preserves active entry hysteresis and uses two
rounded doubled products. Phase bit1 updates its history after amount publication.
The separate decel producer updates both histories only when its old count is0.

Startup run-transition0004.3 suppresses reseeding but retains decrement/gain
refresh. Running context uses literal SEI/CLI, with no implicit restore on failure.
AFR holds, park delay and interval decrement are distinct. AFR and spark decay
products truncate; spark's initial delay decrements only within full phase00..0F.
The existing REF routine separately consumes02C9/0267/0268.

AFR selection tests any003E&A0 bit, caps coolant before open-table lookup and
performs entry-idle filtering before re-evaluating idle. Warm idle qualification
sets readiness on the current call while retaining base AFR; application uses a
later strict timer comparison. Only full phase27 advances idle delay. Hot/warm
biases precede the upper cap; additional REF enrichment follows it and can exceed
that cap. The nonrunning controller copies024A to024B without PE/running overrides.

PE preserves permission and active/full-gain latches separately. Old-count
comparisons, wrapped timer increments and full phases07/17 determine updates.
Vehicle-change0818 is an explicit retained input from the later BLM tail, not a
newly fabricated speed observation. TPS interpolation uses actual FDIV behavior,
then rounded gain application. Exit paths retain gain until their own count gate.

Running service0395.2 overrides AFR0397 and bypasses optional1800. Otherwise,
profiling0086.6 requests `PCM_AFR_EXTENSION`; absent code returns UNIMPLEMENTED,
records the unresolved dependency and leaves024B unchanged. Supplied extension
errors retain their committed prefix. Successful024B publication follows the call.

## Verification and remaining joins

The suite contains476,821 compiled-C/ROM comparisons across742 reachable scoped
instruction starts, with two additional defensive instructions bounded below.
It includes553 selected operation-failure prefixes and1,024 retained-history calls.
It checks mapped state, byte/word bus transactions, literal
IRQ masks, completed slice frames, source defaults and overlapping lookup views.
Production profiles are immutable named descriptors with bounded backing views;
test-only expanded curves/matrices permit arbitrary calibration variants. All540 distinct source-profile bytes, every
overlapping exported default and all3,087 expanded fixture bytes are checked against the
SHA256-verified stock image rather than inferred from disassembly comments.

Sweeps cover authorization and period words, crank coolant/TPS, fractional
MAP/TPS histories, startup gains, open AFR coordinates, idle/PE timers and retained
producer/consumer/REF histories. Selected callback and missing/failed1800 cases
check every operation prefix. Configuration contracts check lookup bounds and
committed prefixes. Two defensive instructions are excluded from execution
coverage with explicit invariants:8996 cannot overflow a rounded filter approaching
an increasing byte target;8BB8 cannot underflow `part-round(ratio*part/256)` for
byte inputs. Both guards remain represented by the C saturating helpers.

Both host routes contain46 checks:23 quick contracts/provenance checks and23 ROM
suites. Broader fuel/slot1/4/D/F roots remain boundaries until their full prefixes
and successors are implemented. BLM/O2 feedback and learning8C73 onward, remaining
pulse corrections, AE accumulation/delivery, EGR producers, ignition/STOP handling,
and852C cleanup remain unfinished. Optional1800 code, target ABI, physical bus
behavior and delivered fuel are separate validation obligations.
