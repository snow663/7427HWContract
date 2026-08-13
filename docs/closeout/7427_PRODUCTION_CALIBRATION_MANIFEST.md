# 7427 Production Calibration Manifest

## Purpose

Replace keyword-only section classification as the authority for replacement-OS calibration ownership.

The existing `CALIBRATION_SOURCE_INDEX.md` remains useful as a searchable source inventory, but its classifier is heuristic. Production ownership in this document is based on executable use and the known `$31` source organization.

Numeric authority rule:

```text
actual BMHM BIN value > source/disassembly operand
```

Semantic/provenance rule:

```text
executable BMHM source/disassembly > comments/keyword classifier
```

When the source and BIN disagree, keep both records but reconstruct stock behavior with the BIN value unless executable behavior proves the source address/width interpretation is wrong.

## Source extract state

`31_HAC_calibration_extract_nowrap.html` contains:

```text
226 sections
11,916 labeled data records
11,431 FCB records
485 FDB records
$4000-$70FF source calibration span
0 parse errors
96 source/extraction warnings retained for review
```

The first `$4000-$400F` source bytes are:

```text
25 17 00 00 00 00 68 8C 31 01 91 04 B7 82 03 10
```

Those bytes agree with the existing raw-ROM-derived BMHM trace report. This is a verified anchor, not a substitute for the remaining full-BIN audit.

## Production-control ownership manifest

### Core identity / lifecycle / feature gates

| Range / labels | Owner | Role | Replacement treatment |
|---|---|---|---|
| `$4000-$4008` | calibration integrity | platform/BCC/checksum/mask identity | Preserve provenance; replacement may use a clean OS/calibration header and its own integrity check. |
| `$4009` | lifecycle | shutdown-delay/time scalar | Preserve semantic shutdown delay; confirm exact stock numeric value from BIN audit. |
| `$400B-$400F` | feature/control gates | AFR/fuel/spark/I/O mode bytes | Do not copy wholesale. Decode only production features intentionally retained. |

### Spark production calibration

| Range | Owner | Production use |
|---|---|---|
| `$4166-$4289` | spark.base_open | open-throttle base spark vs load/RPM |
| `$428A-$43AE` | spark.base_closed | closed-throttle spark vs load/RPM |
| `$43AF-$4439` | spark.coolant | coolant compensation vs load/RPM |
| `$443A-$44BE` | spark.mat | MAT/IAT correction and positive/negative load multipliers |
| `$44BF-$44CF` | spark.wot | WOT spark correction vs RPM |
| `$44D0-$44D4` | spark.transient_timeout | production spark timeout/reduction rate where enabled |
| `$44D5-$44F0` | spark.altitude | baro/vacuum altitude correction |
| `$44F1-$452C` | spark.idle | idle overspeed/underspeed/derivative spark correction and clamps |
| `$452D-$454A` | spark.startup | startup spark magnitude/delay/decay |
| `$454B-$4557` | spark.latency | spark latency vs RPM used by degree/time conversion |
| `$4558-$4584` | spark.load_basis | baro/load basis correction used by spark/load derivation |
| `$4585-$45BD` | spark.knock | maximum knock retard/recovery/knock activity calibration |
| `$45BE-$45DA` | spark.low_octane | learned low-octane retard magnitude and RPM/MAP multipliers |
| `$45DB-$465C` | spark.knock_event_timing | knock-window/event timing thresholds/adders |
| `$465D-$46E3` | spark.knock_window | knock-window delay vs RPM / TOC1 timing input |
| `$46E4-$46F8` | spark.burst_knock | burst-knock qualifiers/magnitude/time |

Excluded from the clean default feature set even if adjacent to spark:

```text
EGR-specific spark correction
transmission torque-management spark
service-tool forced spark overrides
```

They become new feature-scope items only if intentionally enabled.

### Fuel production calibration

| Range | Owner | Production use |
|---|---|---|
| `$48F7-$4913` | fuel.closed_loop_modes | BLM/closed-loop window/mode behavior |
| `$4914-$4949` | fuel.afr_pe_trim | AFR, PE, proportional correction and fuel trim parameters |
| `$494A-$494E` | fuel.o2_idle_threshold | idle O2 thresholds and proportional timing constants |
| `$494F-$4974` | fuel.closed_loop_correction | proportional/integrator fuel correction; **must not be excluded as transmission merely because nearby comments mention mode context** |
| `$4979-$4987` | fuel.low_pw | low-BPW correction/offset when selected |
| `$4988-$4998` | fuel.battery | BPW/battery correction multiplier |
| `$4999-$49A9` | fuel.protection_afr | airflow-indexed AFR protection target where retained |
| `$49AA-$49D4` | fuel.altitude | BPW altitude correction vs baro/MAP |
| `$49D5-$4A87` | fuel.ve_open | primary open-throttle/open-load VE table family |
| `$4A88-$4AE2` | fuel.ve_closed | closed-throttle fuel/VE table family |
| `$4AE3-$4B04` | fuel.temperature_model | MAT/coolant interaction used by fueling model where enabled |
| `$4B05-$4B16` | fuel.injector_bias | injector offset/bias vs battery voltage |
| `$4B17-$4B49` | fuel.decel_enlean | decel coolant/MAP/TPS reductions and MAP filtering |
| `$4B4A-$4BAC` | fuel.accel_enrich | MAP/TPS pump-shot, baro/temp/MAT/RPM corrections |
| `$4BAD-$4C5A` | fuel.open_loop_afterstart | open-loop AFR, afterstart/choke decay and airflow multipliers |
| `$4C5B-$4C8C` | fuel.power_enrich | WOT/PE entry, delay, AFR and baro/TPS qualification |
| `$4C8D-$4C9C` | fuel.dfco | DFCO RPM/TPS qualifications |
| `$4C9D-$4CE0` | fuel.crank_transition | crank-to-run AFR transition and decay |
| `$4CE1-$4D91` | fuel.closed_loop_trim | O2 thresholds, integrator/proportional delays/gains and flow/MAP/RPM gains |
| `$4D92-$4D9A` | fuel.engine_injector_constants | engine/injector-size conversion constants |
| `$4D9C-$4E25` | fuel.crank | startup BPW, RPM/baro/TPS and DRP-count crank multipliers |
| `$4E26+` crank subsection | fuel.crank | >24-DRP cycling crank multiplier and associated crank thresholds before IAC/diagnostic material begins |

The `$4E26-$4E91` extractor section is mixed-content and must not be owned by a single keyword-derived subsystem. Executable address/use decides ownership item by item.

### IAC / idle-air production calibration

| Range | Owner | Production use |
|---|---|---|
| `$4E8F-$4E91` | iac.mode_init | IAC mode words / pre-start movement threshold context |
| `$4E92-$4EA5` | iac.flow_to_steps | desired airflow to IAC step-position linearization |
| `$4EA6-$4EC1` | iac.altitude | altitude correction and IAC baro scaling |
| `$4EC2-$4EE8` | iac.cold_start | cold offset flow and decay/delay |
| `$4EE9-$4F31` | iac.enable_transition | flow multiplier, closed-loop enable delays, startup/transition constants |
| `$4F32-$4F6D` | iac.target_rpm | desired idle RPM families for P/N, drive, A/C states |
| `$4F6E-$4F91` | iac.start_init | not-running/start initialization target and transition values; do not classify as EVAP from unrelated nearby text |
| `$4F92-$4FCB` | iac.integral_gain | integral gain families vs RPM error/state |
| `$4FCC-$503B` | iac.proportional | proportional airflow correction tables vs RPM error/state |
| `$503C-$5056` | iac.derivative | derivative airflow and filter coefficients, including fast/slow coefficients `$503A/$503B` |
| `$5057-$50A2` | iac.throttle_follower | follower gains, TPS/VSS/coolant/RPM filtering and follower behavior |
| `$50A3-$50E8` | iac.transient_dfco | IAC-air transient/AE coupling and DFCO additional-air correction |
| `$50E9-$5124` | iac.return_kicker | TPS return/throttle-kicker/return-control calibration where retained by the clean feature set |

A replacement may simplify optional throttle-kicker/power-steering/A/C branches when the associated physical feature is absent, without reopening the core IAC extraction.

### Sensor scaling / validation

Sensor conversion and plausibility scalars are retained only when their executable use is tied to a retained sensor. Core retained input families include:

```text
MAP
TPS
coolant
MAT/IAT if configured
battery
O2
baro/load basis
REF/DRP period/RPM
```

The exact physical voltage/pin transfer belongs in endpoint setup/test-confirm; calibration contains software scaling/threshold values only.

### Diagnostic / fallback calibration

Replacement-relevant defaults and thresholds include at minimum:

```text
L4E68-L4E6A  MAP substitute/default model
L4E77         knock-sensor-fail fixed spark retard
L5B17         coolant invalid default
L5B22         TPS invalid default
L4E48         MAT invalid default
REF/DRP timeout/run qualification thresholds
battery/key-off qualification thresholds
IAC operating-voltage/park/reset thresholds
calibration integrity/version/checksum policy
```

The full OEM diagnostic mask/counter area is not itself a tuning requirement. Retain the semantic threshold/default for faults that alter production control.

## Excluded stock calibration by default

Unless a retained hardware feature requires it:

```text
EGR / EVRV
EVAP / purge
4L60/4L80 shift scheduling
TCC
force-motor / transmission pressure
gear-adaptive shift data
transmission torque management
factory test
remote-broadcast/OEM bookkeeping
service-only forced-control constants
```

## Required BIN audit

Run:

```text
python tools/audit_calibration_against_bin.py \
  --extract 31_HAC_calibration_extract_nowrap.html \
  --bin BMHM_95_C-G-K_Truck_7_4TBI_4l80.bin \
  --audit maps/closeout/calibration_bin_audit.csv \
  --overlay maps/closeout/calibration_bin_correction_overlay.csv
```

Completion rule:

- every `MISMATCH` row is reviewed;
- BIN bytes are the stock numeric value unless an address/width interpretation is proven wrong;
- `ODD_WORD_ADDRESS_REVIEW` and `NEXT_LABEL_DELTA_*_REVIEW` rows are checked for address-label/word-width mistakes;
- the correction overlay is committed even if it contains only a header/no mismatches;
- only then may `calibration/tuning` be frozen at 100%.
