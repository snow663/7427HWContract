# Spark load, plausibility and run admission

Authority is the recorded stock BMHM image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The callable prelude covers A466..A5E4 and stops at the A5E5 normal continuation,
the resident AC51 alternate path, or the first SWI boundary at A5D7.
The SWI instruction, its handler/frame and the following trap loop are outside
this host implementation. The [complete resident controller](spark_controller_contract.md)
now connects the implemented bodies and their normal monitor.

## Routine ownership

| Routine | ROM scope | Responsibility |
|---|---|---|
| `pcm_spark_load` | A466..A4B2 | Distinct vacuum, load and normalized-load coordinates |
| `pcm_spark_map_check` | A4B3..A4EB | MAP plausibility counter and paired fault indications |
| `pcm_spark_fuel_admit` | A581..A59A | Independent fuel-running qualification |
| `pcm_spark_timeout` | A5C6..A5D9 | Timeout state and board-bit clear before the first SWI |
| `pcm_spark_admit` | A4EC..A580; A59B..A5E4 | Reference consumption, running/startup gates and no-reference routes |
| `pcm_spark_prepare` | A466..A5E4 | Ordered load→MAP check→admission wrapper |

Each public routine has its own file. `normal=true` identifies the A5E5
continuation only. An AC51 dependency return leaves it false, including a
successful supplied binding; the caller must not then run the normal command
builder. A failure or trap boundary also leaves it false. A null output pointer
returns `PCM_BAD_CONFIGURATION` before any state work.

## Named state

| Factory location | C field | Ownership |
|---|---|---|
| 01C6,02F4 | `spark.map_filtered`, `barometric_high` | Explicit MAP/BARO inputs; 02F4 is the high byte of the BARO filter |
| 01CE,0257 | `normalized_load_divisor`, `density` | Explicit upstream normalization inputs |
| 01C9,01C0,01CF | `vacuum`, `load_coordinate`, `normalized_load` | Three different produced coordinates |
| 0018.4,006F.3,0229 | `map_fault`, existing raw `load_status`, `map_fault_count` | Paired indications and byte counter |
| 082E,0061,01D9 | Existing `reference.map_sample`, `spark.rpm_low_coordinate`, `reference.throttle` | Plausibility/admission inputs |
| 0050.5,0050.2 | Existing `reference.pending`, new `consumed` | One-bit reference request and consumption indication |
| 004F.4,004F.7 | Existing `runtime.fuel_running`, `spark_running` | Independent shared running states, now explicitly volatile |
| 0044.3,0004.3 | `spark.first_reference`, `run_transition` | First-reference latch and transition indication |
| 004F.6,0051.6 | `startup_gain_enabled`, `startup_gain_complete` | Separate startup update gate and completion latch |
| 01F2 | Existing `startup_recovery_gain` | Same word later used by decel recovery |
| 0211,0210,0202 | `fuel_run_count`, `spark_run_count`, `missing_reference_count` | Byte admission counters |
| 0260,01EA,005F | `reference_age`, `adaptive_period`, `period_basis` | Word age, adaptive term and later period-conversion basis |
| 02CE | Existing `reference.event_age` | IRQ-owned byte subject to the masked cap |

Old addresses establish provenance, not a target RAM layout. The new fields
are included in existing struct clears. Remaining factory reset stages and
upstream MAP/BARO/density/input production keep their separate ownership.

## Load coordinates and MAP plausibility

Define `K(x)=hi(min(65535,2*(151*x+64)))`. Sample BARO high and MAP; use their
positive difference, or 1 when BARO<=MAP. Store the byte negation of K at 01C9.
Sample MAP again and store `K(max(MAP-26,0))` at 01C0. The normalized coordinate
uses the HC11 fractional quotient `Q(density,divisor_byte<<8)`: zero divisor or
numerator>=divisor selects FFFF. Store
`hi(min(65535,2*max(Q-8192,0)))` at 01CF. No hardware or calibration binding is
needed for these fixed-immediate operations.

The MAP check clears both fault indications first. Existing 006F.2, or raw
MAP>=4E64, clears 0229. Otherwise old 0229>4E66 sets 0018.4 and 006F.3 and retains
the counter. At/below the count threshold, RPM61<4E65 or TPS>4E67 increments the
byte with wrapping; other cases clear it. Thus a threshold of 255 permits a
255→0 wrap rather than a saturating count or an immediate fault.

## New-reference qualification

Consume 0050.5, set 0050.2, clear word 0260, and replace 01EA with
`v=u16(old-(old>>3)-1); result=0 if v&0x8000 else v`. The N-bit decision follows
word wrapping; it is not an unrestricted signed or unsigned minimum. Clear 0202.

Fuel-running qualification reads a fresh 3FC0 word. At/above 4135, clear 0211.
Below it, increment a local byte; reaching 4143 sets 004F.4 and clears 0211.
A wrapping increment is compared after the wrap. This helper is called only
where the caller finds fuel-running clear.

With spark-running already set, this helper may run before a fresh test of
004F.6 and 0051.6. Enabled, incomplete startup updates 01F2 with
`lag8(255,old,414E)` while old<=0xFEF0. Above that threshold set completion and
retain the word. The same 01F2 field remains shared with decel recovery.

Without spark-running, the first reference sets 0044.3 and tail-exits through
AC51 before fuel qualification. Subsequent references may qualify fuel, then
read 3FC0 again for spark qualification. The two period reads are separate
inputs; the first must not be cached for the second. Period>=4133 clears 0210
and exits through AC51. Otherwise increment 0210 as a byte; below 4142 exits
through AC51. Reaching the threshold sets spark-running, clears 0210, sets 0004.3,
clears startup completion and resets 01F2=0 before normal continuation.

## No-reference and timeout routes

Below 4962, increment and store word 0260; otherwise retain it and write 306F=0.
Use the resulting counter held by this call for the 0x00A0 threshold. At/above it,
assign SEI and cap 02CE downward to 4D96 when needed. Then assign CLI on **every**
successful path, including calls that skipped SEI and calls entered masked.
The counters count admitted calls; no new physical time units are inferred.

At 0202>=0x17 (23), clear fuel/spark-running and 0044.3, write 005F=FFFF, then perform
the literal read/clear-mask0x10/write transaction at 3060. Successful completion
returns the new `PCM_TRAP_BOUNDARY` before SWI. Failure retains the completed
prefix; target trap execution, frame preservation and recovery are separate
implementation work. In particular, this status does not claim a normal factory
return from the trap loop.

Below that missing-reference count, a nonrunning call exits through AC51.
A running call increments 0202 and admits A5E5 without the event decay above.
An IRQ-like fixture setting the pending flag during CLI leaves that request
for the next call while later running-state gates sample their new value.

## Calibration and error contracts

| Source | Stock | Field |
|---|---|---|
| 4133,4135 | 0888,0CCC | Spark/fuel period thresholds |
| 4142,4143 | 02,02 | Spark/fuel event thresholds |
| 414E | A0 | Startup gain |
| 4962 | 00F0 | Reference-age write threshold |
| 4D96 | 05 | Event-age cap |
| 4E64..4E67 | 0A,40,02,1A | MAP sample, RPM, counter and TPS thresholds |

These 14 distinct calibration bytes match the stock image. Fields live in the
existing immutable source profile, independent of the future serialized format.
Missing calibration/profile returns BAD_CONFIGURATION from MAP, fuel-admission
and admission routines. The prepare wrapper retains any preceding load writes.
The load and direct-timeout routines do not require calibration.

Missing hardware returns NO_HARDWARE. Production AC51 now runs the implemented
resident body without a task binding. This earlier slice suite alone links a
substitute adapter, with explicit success/state fixtures and missing-dependency
returns. The newer complete-controller suite links the real adapter. Failure injection checks
every event position in selected read, write, mask and dependency histories.

## Verification and next work

620,169 additional compiled-C/ROM comparisons cover 134,135 load cases,
135,168 MAP cases, 131,072 fuel cases, 210,944 reference/startup/age cases,
6,144 fresh-period/alternate/trap witnesses, 2,048 calibration/state variants,
274 failure prefixes and 384 history calls. All 155 instruction starts before
the trap boundary in A466..A5E4 execute; A5D7 SWI and A5D8's following loop
branch are deliberately excluded. Completed fragments and the fuel helper
balance the ROM local stack. Tests compare mapped state, ordered I/O widths
and mask/task events, final mask, normal route and unresolved dependency.

Coverage includes all MAP/BARO byte pairs, all plausibility count/limit pairs,
all raw-period words with selected limits, all fuel count/event-limit pairs,
every adaptive-decay/startup-gain/reference-age word under selected profiles,
fresh period samples, unrelated flag bits, and selected callback-time input
changes. These are not every state combination or interrupt interleaving.
Coherent fixture period words do not prove physical counter coherency.

Both host routes now contain 38 CTest entries. The inventory is 161 public
routines: 73 implemented outlines, 41 explicit boundaries and 47 algorithms.
The [normal period/RPM preparation](spark_period_contract.md) is now implemented.
The [output/alternate bodies](spark_output_contract.md) are now implemented.
The [monitor and resident controller](spark_controller_contract.md) are now implemented. Target ABI, physical backend,
memory/stack fit and cycle timing remain separate verification.

See the [command contract](spark_command_contract.md),
[upstream fuel inputs](../../docs/analysis/FACTORY_UPSTREAM_FUEL_CALCULATIONS.md),
[upstream admission](../../docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md)
and [period handoff](../../docs/analysis/FACTORY_SPARK_INTEGER_HANDOFF.md).
