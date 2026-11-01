# Base and environmental spark construction

Authority is the recorded stock BMHM image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
This step implements the contiguous A700..A84D composite calculation and the
complete CA6B..CB14 auxiliary producer. The [resident controller](spark_controller_contract.md)
now joins this body. The [slot7 wrapper](slot7_contract.md) calls the auxiliary
producer directly between named background-IAC and shift-lamp dependencies.
The composite at 01FD from this slice feeds the now-implemented
[idle/transient/decel body](spark_modifiers_contract.md) and
[command body](spark_command_contract.md), under the optional 1812 dependency.
The [output conversion](spark_output_contract.md) is now implemented; physical
EST semantics and target execution remain separate work.

## Module ownership

| Routine | ROM scope | Responsibility |
|---|---|---|
| `pcm_spark_base` | A700..A72C | Two load-history latches, retained idle-table selection, piecewise RPM and base lookup |
| `pcm_spark_coolant` | A72D..A763 | Load/vacuum mode, transformed coolant row and cold-idle floor |
| `pcm_spark_altitude` | A764..A779 | Optional altitude lookup; disabled retains the term |
| Existing `pcm_low_octane_retard` | A77A..A791 | Two rounded adaptive products |
| `pcm_spark_egr` | A792..A7D6 | EGR column transform, filtered word, inactive bias reset |
| `pcm_spark_sum` | A7D7..A81D | Wrapped word rounding, additions and bias/retard subtraction |
| `pcm_spark_mat_effect` | A81E..A84D | Signed MAT addition/subtraction using a truncated product |
| `pcm_spark_terms` | A700..A84D | Ordered calls to all seven slices above |
| `pcm_spark_mat` | CA6B..CAB3 | MAT enable/temperature gates and wrapped sign/magnitude production |
| `pcm_spark_pe` | CAB4..CAD4 | Coolant/fault/PE gates and rounded PE fraction |
| `pcm_spark_auxiliary` | CA6B..CB14 | MAT, PE and the existing knock-gain producer |
| `pcm_lookup2d` | F4DE..F54F | Offset floors, row-product byte wrap, three rounded interpolations |
| `pcm_lag8` | F459..F478 | Byte-target, word-state filter with explicit signed floor division |

Each public routine has its own file. The new state lives in `PcmSpark`; shared
coolant/RPM/TPS, PE/fault state and adaptive-knock fields retain their existing
owners. The earlier01C1 load becomes01C2, then current01C0 becomes01C1. The learner
continues to consume the older01C2 latch.

Base table selection samples retained0050.6 before later idle control can
update it. RPM61<=64 is used directly; otherwise use saturating RPM62+16.
Coolant values above176 use `2*(min(coolant,208)-88)`; lower values pass through.
Its cold-idle floor uses a fresh coolant sample. These input samples retain
their own gates rather than being combined into one global snapshot.

## Calibration tables and lookup semantics

`PcmCalibration.spark` points to an immutable `PcmSparkCalibration` profile.
The source defaults are in `calibration/spark_tables.c`; the profile and its
arrays can live in ROM. This pointer/struct representation is not a serialized
EEPROM format. Allocation and future calibration placement remain ours.

| Header | Profile table | Row offset | Column offset | Stride | Backing values |
|---|---|---:|---:|---:|---:|
| 4166 | `base_normal` | 0 | 0 | 17 | 289 |
| 428A | `base_idle` | 0 | 0 | 17 | 289 |
| 43AF | `coolant` | 16 | 0 | 9 | 144 |
| 44D5 | `altitude` | 96 | 176 | 6 | 66 |
| 443A | `mat` | 80 | 0 | 12 | 109 |
| 4860 | `egr` | 16 | 0 | 13 | 79 |

Backing arrays include every byte read for the declared caller input domains,
including neighboring cells with zero interpolation weight. The original lookup
has no general upper-axis clamp; reduced nominal table sizes would omit reads.
Some views consequently overlap adjacent factory calibration fields. Their
default values agree, and the host adapter applies shared-address variants to
every affected view. The new source arrays are independently allocated views,
not a requirement to preserve overlapping calibration placement in the new BIN.

F4DE subtracts each axis offset with zero floor. With adjusted row r and column c:

```text
first  = u8((r >> 4) * stride) + (c >> 4)
second = first + stride
below  = interpolate(values[second], values[second+1], u8(c << 4))
above  = interpolate(values[first],  values[first+1],  u8(c << 4))
result = interpolate(above, below, u8(r << 4))
```

Each interpolation rounds the absolute difference product by128, then adds or
subtracts the step according to slope. Column interpolation is rounded twice,
then row interpolation is rounded. A single combined bilinear expression loses
those integer results. F501's ABX uses byte B of the preceding MUL, so the
row-index×stride product wraps before adding the column and second stride.

The C helper validates both neighboring rows/columns before reading, even at
zero weight. Missing storage or a too-short declared backing returns
`PCM_BAD_CONFIGURATION` and retains the output parameter. The ROM has no bounds
error return; these invalid-profile checks are C contracts, not claimed ROM
equivalence cases. Changed profiles can supply larger arrays. A 527-byte test
view covers every byte-stride geometry, including endpoint index 526.

The spark-terms comparison verifies 1,095 distinct calibration bytes: 1,035 new and 60
previous/shared. These include table headers and reachable backing, scalar
mode/bias/threshold fields, MAT coefficients, PE curve and the reused adaptive
and knock curves. Independent views do not inflate the distinct-byte count.

## Retained state and arithmetic

- Disabled altitude400D.2 retains01FB. Its bias still participates in the sum.
- Disabled MAT400B.6, or MAT below80, zeros01FA while retaining0041.1. Otherwise
  cap MAT at192; select RPM<=176 or zero-floored vacuum-80 for the column.
  Subtract413F as a byte. Classify the wrapped result's N bit, then byte-negate
  a negative magnitude. This is not an unlimited signed subtraction.
- PE defaults01FC to zero. Require coolant strictly above45DA, sensor fault
  clear and PE003D.5 set. Multiply the RPM curve by0278 with rounding.
- Inactive EGR writes413E<<8 to01F4. Active EGR first samples the high byte01B2;
  mode0 uses high(192*sample). Other modes use wrapped-negative vacuum, doubling
  through64, otherwise halving its excess and adding128 with a cap at192.
  The row is min(RPM62,160)>>1.
- EGR filtering computes `old + floor((((target*256)-old)*gain+128)/256)`.
  C's negative division truncates toward zero, so `pcm_lag8` implements floor
  explicitly. Gain and old word are sampled at their own producer positions.
- EGR rounding for the composite first wraps `word01F4+128` at16 bits, then
  takes its high byte. Add altitude, base, PE, coolant and startup02CB. Subtract
  biases413B..413E, conditional55F2 when00A4's low nibble is nonzero, adaptive020B
  and transmission015A, propagating borrow in the wrapped word result.
- The MAT effect interpolates a sign-selected load curve, then takes the high
  byte of coefficient×magnitude **without rounding**. Publish083C, sample the
  sign again, and add/subtract from01FD with word wrap.

At A7D7 the ROM's incoming D is the EGR word just stored at01F4. The standalone
sum fixture supplies that D explicitly; the C API consumes producer-owned
`spark.egr_filtered`. The contiguous wrapper preserves this ownership and
state handoff. This is not a claim about arbitrary concurrent writes to that
word or every possible interrupt interleaving.

## Failure prefixes and verification

Missing root/profile calibration returns `PCM_BAD_CONFIGURATION`. Pure routines
need no platform I/O binding. A base-table failure retains the already shifted
load latches but does not publish the new base value. A later table failure in
the combined body retains all earlier committed terms. Disabled/inactive paths
do not require their unused matrix storage. No rollback or target recovery is
invented.

The suite adds 753,561 C/ROM comparisons: 262,288 matrix/filter cases, 82,176 base
cases, 135,689 coolant/altitude/EGR cases, 132,608 MAT cases, 136,192 PE/composite
cases, 2,048 bounded variants, 2,048 auxiliary→composite witnesses and 512 retained
history calls. All 336 scoped instruction starts execute. The ROM side checks
local stack balance and the math helpers' preserved registers; it performs no
hardware transactions in these slices.

The earlier source suites remain, bringing CTest to 28 checks. There are 141 public
routines: 65 implemented outlines, 41 explicit dependency boundaries and thirty-five
algorithms. Target ABI, memory/stack fit and physical timing remain separate work. Idle/transient/decel corrections
and resident override/limits/service edits are now implemented. The
[normal period/RPM preparation](spark_period_contract.md) is also implemented.
The [output/alternate bodies](spark_output_contract.md) are also implemented;
the [monitor and resident controller](spark_controller_contract.md) are now implemented; optional modules retain explicit boundaries.

See the [adaptive spark contract](adaptive_spark_contract.md),
[factory upstream derivation](../../docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md)
and [shared arithmetic closure](../../docs/analysis/FACTORY_ENGINE_CALCULATION_CLOSURE.md).
