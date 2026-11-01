# Spark conversion, ordered publication and alternate RPM

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
This step implements AB44..ABCA output conversion/publication and a callable
AC51..ACA6 alternate body. The following [controller contract](spark_controller_contract.md)
now implements the ABCB..AC50 monitor and connects both resident adapters to dispatch.
Optional 180F/1812 implementations and their target machine ABIs remain unsupplied.

## Routine ownership

| Routine | ROM scope | Responsibility |
|---|---|---|
| `pcm_spark_coordinates` | A5FE..A628; AC71..AC9A | Shared wrapped-divisor quotient and two RPM coordinates |
| `pcm_spark_output_extension` | AB62..AB68 | Optional 180F argument/result boundary |
| `pcm_spark_convert` | AB44..AB88 | Sign, byte magnitude, startup gain, latency and saved timing word |
| `pcm_spark_handoff` | AB89..ABCA | Anchor selection, four reads and four ordered word writes |
| `pcm_spark_output` | AB44..ABCA | Conversion followed by publication |
| `pcm_spark_alternate` | AC51..ACA6 | Actual alternate-body calculation and flag clears |
| `pcm_spark_publish` | Conditional normal A466..ABCA | Build then publish, with a completion result |

Each public routine has its own file. Normal period sampling now uses the same
pure coordinate helper as the alternate body. Production `pcm_alternate_rpm`
now calls that body directly, and `pcm_spark_control` follows completed publication
with the monitor. This output-only suite retains a link-time alternate boundary
fixture to preserve its scoped comparisons; the newer complete-controller suite
links both real adapters. Publication alone still stops before the monitor.

## Interfaces and conversion

| Location | C interface | Contract |
|---|---|---|
| 004F.0 | `spark.command_negative` | Classification from command bit15, sampled again after the hook |
| 0201 | `spark.output_latency` | Published byte latency lookup result |
| 004B.4 | `spark.output_request` | Cleared by the alternate body; later normal monitor is its other owner |
| Register A at180F | `extension_magnitude` | C dependency payload, not an invented factory RAM byte |
| AB89 saved stack word | Local `saved` argument | Native C value, not a pointer into a factory frame |

Clear 004F.0. Read 01EE; when bit15 is set, set 004F.0 and byte-negate its low byte.
Otherwise use the low byte unchanged. This is an 8-bit coefficient, not a 16-bit
absolute magnitude passed to multiplication.

With startup completion 0051.6 clear, read the high 01F2 byte and increment it as
a byte when bit7 of the separately sampled low byte is set. FF80/FFFF can wrap
the multiplier to zero. Replace magnitude with
`u8(high(magnitude*multiplier)+1)`: the product truncates, and the increment is
unconditional. With completion set, skip this scaling entirely.

The same 0086.6 flag used by profiling and 1812 gates the 180F hook. Its new
`PCM_SPARK_OUTPUT_EXTENSION` dependency receives and returns the magnitude
through the C payload. An inactive hook requires no binding or calibration.
A missing active binding returns UNIMPLEMENTED and identifies the task.
The caller's magnitude is updated only after successful return. Tests supply
well-formed returns and selected state/register changes; they do not implement
the module or establish its register/stack ABI.

After the hook, sample 0062 and look up the capped zero-offset curve at 454A.
Store the result at 0201. Capture the magnitude across this lookup as the ROM
does with PSHA/PULA. Use the existing rounded word gain with basis 005F.
Sample 004F.0 again: retain the product for negative command, negate it as a word
otherwise. Subtract the current 0201 byte with word wrap to obtain `saved`.

## Handoff reads and writes

Let p be a fresh 3FC0 read. Compute:

```text
anchor = (u16(-p)>>4) | 0xF000
candidate = u16(anchor + first_read(3FF6))
chosen = saved if u16(candidate-saved)&0x8000 else candidate
first = u16(chosen - second_read(3FF6))
```

The branch tests N only; it is not a signed minimum. At p=0 the anchor is F000;
for nonzero p it equals the wrapped negative ceiling of p/16. The two rolling
reads remain distinct inputs. Publish these transactions in order:

| PC | Transaction | Value |
|---|---|---|
| ABAA | Write16 3FE8 | `first` |
| ABB0 | Read16 3FDC | Fresh work value |
| ABB3 | Read RAM01EC | First correction sample |
| ABB7 | Read RAM01EC | Second correction sample, latched before the next write |
| ABBA | Write16 3FE6 | `u16(first+work-first_correction)` |
| ABC0 | Write16 3FDC | Latched second correction |
| ABC8 | Write16 3FF6 | `chosen` |

There are four peripheral reads overall and four writes. Both 01EC samples are
explicit volatile reads. A callback changing 01EC during the 3FE6 write must not
change the already-latched 3FDC publication. Selected mutations after 3FE8 or the
3FDC read verify that earlier correction values are not cached across those
transactions. These witnesses do not cover every instruction-level interrupt.

Interleaved F3ED calls are actual RTS instructions. No imaginary delay-body or
extra delay callback is introduced. Target C call/stack/cycle costs still need
their own validation; host ordering does not establish physical ASIC behavior.

## Alternate path and completion

With first-reference 0044.3 clear, set 005F=FFFF and retain raw period, both RPM
coordinates and normal filters. With it set, sample 3FC0 into 005F and 01E8, use
the same optional 4141 scaling and wrapped-divisor transform as the normal path,
and publish 0061/0062. Retain 083D,0063/0064,0067/0068,028E,0837 and timing terms.
Both successful exits clear 004B.4 and 0050.2. The inactive path needs neither
profile nor hardware. The active path validates its profile and retains all
state if the first hardware read fails.

`pcm_spark_publish(pcm,&published)` sets its result true only after successful
normal build and all four publication writes. An alternate return, trap boundary
or failure leaves it false. Earlier writes remain committed; false does not
mean rollback. This wrapper stops before the ABCB monitor. The existing 3060/
306F admission transactions remain part of its earlier prefix.

## Calibration and failures

454A contains stock cap C0. The 14-knot backing at 454B..4558 is:
`00 00 01 05 0A 0A 0A 0A 0A 0C 0C 0A 0A 20`.
The 4558 neighbor is read even at zero weight at the cap. These 15 distinct
calibration bytes are newly represented in C; the expanded fixture now verifies
all 1,197 stock bytes, including the newer monitor defaults. Alternate scaling reuses the existing 4141 field.
Changed caps can use explicit 17-knot test profiles with supplied extra backing;
the factory default retains 14 knots. Native profile/storage placement remains
independent of the factory address overlap and serialized layout.

Null scalar/completion outputs and missing required profile return
BAD_CONFIGURATION. Invalid accessed latency backing fails after the sign/startup
prefix but before 0201 publication. The standalone handoff needs no calibration.
Missing hardware or callback failures return at the successful prefix, including
partially written peripheral outputs. Host statuses are development contracts,
not new error-return instructions in the original ROM. Target trap/recovery and
physical output dispositions remain separate decisions.

## Verification and next work

The new C/ROM suite exercises all 104 instruction starts in AB44..ABCA and
AC51..ACA6, compares mapped RAM/peripheral state, ordered I/O widths, mask state,
hook payloads, unresolved dependencies and publication completion, and checks
completed ROM local frames. Pure shared-coordinate tests use three actual
instruction fragments before their caller's stores. Joined alternate cases
execute the actual resident AC51 body; 180F/1812 use explicit fixtures.
Normal joined cases stop before ABCB, and timeout cases stop before SWI.

The corpus covers every command word, every startup-gain word, every magnitude/
multiplier pair, every RPM/cap pair with nonflat expanded backing, every saved
word and anchor-period word, every wrapped branch difference, alternate gate/
flag retention, independent rolling samples, selected callback-time changes,
failure prefixes and repeated publication histories. The suite adds 603,682
comparisons: 65,536 coordinate cases, 4,096 hook witnesses, 262,144 conversion
cases, 196,608 handoff cases, 69,632 alternate cases, 4,236 joined witnesses,
1,174 failure prefixes and 256 history calls. These are not whole-program or
physical equivalence claims.

Both host routes contain 28 CTest entries. The source inventory is 141 public
routines: 65 implemented outlines, 41 explicit boundaries and 35 algorithms.
The [monitor and resident controller](spark_controller_contract.md) are now implemented. Startup/vector
assembly, native ABI, memory/stack fit and physical timing/backend checks remain.

See the [period/RPM contract](spark_period_contract.md),
[command contract](spark_command_contract.md),
[integer handoff](../../docs/analysis/FACTORY_SPARK_INTEGER_HANDOFF.md)
and [factory output contracts](../../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md).
