# Spark override, signed limits and service command construction

Authority is the recorded stock BMHM image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The new command wrapper covers A9E0..AB43. Joined with the existing composite
body, the callable calculation covers A700..AB43 under an explicit optional 1812
dependency. These are RAM command calculations; the period/EST conversion at
AB44 and physical output transactions are not implemented by this step.

## Routine ownership and order

| Routine | ROM scope | Responsibility |
|---|---|---|
| `pcm_spark_extension` | A9E0..A9E6 | Gate the unsupplied 1812 module using the shared 0086.6 flag |
| `pcm_spark_override` | A9E7..AA19 | Optional resident override and entry/retained TPS hysteresis |
| `pcm_spark_upper_limit` | AA1A..AA32 | Wrapped reference subtraction and signed upper limit |
| Existing `pcm_knock_corrections` | AA33..AADB | Burst followed by normal knock correction |
| `pcm_spark_lower_limit` | AADC..AB19 | Transmission/recovery/normal signed lower limit |
| `pcm_spark_service` | AB1A..AB43 | Post-limit service edits and both common RAM stores |
| `pcm_spark_command` | A9E0..AB43 | Ordered command construction, stopping at the first failed prefix |
| `pcm_spark_calculate` | A700..AB43 | Existing composite calculation followed by command construction |

Each public routine has its own source file. The broad A466 root and slot7
remain dependency boundaries because their other callees are unfinished.
Auxiliary→calculate sequences in tests supply a chosen producer/consumer order;
they do not replace the factory dispatcher or assert a new cadence.

## State interfaces

| Factory location | C field | Use |
|---|---|---|
| 0086.6 | Existing `scheduler.profiling_enabled` | Also gates the 1812 call; it is not a second independent flag |
| 0036.5,0053.4 | `spark.override_request`, `override_active` | Resident override request and retained admission latch |
| 0006,01D9 | Existing `reference.coolant`, `throttle` | Override admission and lower-limit selection |
| 015A,00A4 | Existing `spark.transmission_retard`, `transmission_status` | Transmission floor admission/precedence |
| 0051.5 | Existing `spark.recovery_active` | Shared decel/recovery floor selection |
| 003B.4 | Existing `runtime.engine_service` | Service-edit admission |
| 0395,0398 | `spark.service_flags`, `service_amount` | Raw service bits and unsigned byte amount |
| 01FD | Existing `spark.composite` | Input word; may be replaced by the resident override |
| 01EE,01F0 | Existing `spark.command`, new `command_latched` | Working command and unconditional post-service latch |

The flag and byte fields preserve their separate gate samples. Named fields
are source interfaces; old addresses are provenance rather than a target RAM
layout. Existing reset-struct clears include the new fields. Remaining factory
reset stages and the producers of these admission/service inputs are separate
work.

## Optional 1812 boundary

A clear 0086.6 skips 1812 without requiring calibration or a platform binding.
A set flag calls the new `PCM_SPARK_EXTENSION` task. An absent implementation
returns `PCM_UNIMPLEMENTED` and records that unresolved task. Earlier composite
writes remain visible, and later command steps do not execute. Callback errors
also stop at the current prefix.

The callback is a host development interface. The resident ROM does not supply
the 1812 implementation, and this step does not infer its register/stack ABI,
hardware purpose or successful behavior. Differential witnesses either stop at
the entry or supply a deliberately well-formed fixture return: no state effect,
a composite/flag change, or an override-input change. The fixture clobbers
registers and returns through a real ROM RTS. Those chosen effects check the
resident continuation, not a reconstructed module. See the
[readback observation](1800_readback.md) for the independent test's limits.

## Resident override

If 4E90.1 is clear, retain both the composite and the prior 0053.4 latch.
If enabled, require 0036.5 and coolant strictly greater than 4161. Select the TPS
threshold from 4164 when the entry latch is clear, or 4165 when it is set.
TPS less than or equal to that threshold writes word 4162 into 01FD and sets the
latch. Any enabled qualification failure clears the latch and retains 01FD.

Stock 4E90=01 disables this override. Stock 4161=FF also makes the coolant gate
unreachable for a byte input. Enabled variants are explicit supplied test
profiles; source defaults and the truck tune are not changed to enable them.

## Upper limit, knock, lower limit

First write `u16(composite-reference_bias)` into 01EE, using byte 4132 as the
bias. Compare that result and word 4144 as signed 16-bit values; retain the lesser.
Equality still executes the
ROM store. The C uses XOR 8000 ordering of unsigned words, avoiding a narrowing
unsigned-to-signed cast whose result would depend on the C implementation.

Next execute the already checked burst and normal-KR routines. Their word
subtractions wrap. Normal-KR preserves the literal SEI/read 020D/clear/CLI
sequence and its zero, retained, fault and capped-update routes.

Select the lower bound in this order:

| Admission | Selected word |
|---|---|
| Nonzero 015A and 00A4.3 set | 414A |
| Otherwise nonzero 015A and any 00A4 mask 17 bit set | 414C |
| Otherwise 0051.5 set and TPS<=48DA | 4148 |
| Otherwise | 4146 |

The two 00A4 tests remain fresh samples. Compare the selected floor and 01EE as
signed 16-bit values and retain the greater, including an equal-value store.
This does not assert an unsigned clamp or combine both bounds into one call:
knock correction occurs between them, and service edits occur afterward.

## Service edits and common commits

Read 01EE. When 003B.4 and 0395.3 are both set, clear the local command unless
0395.4 is set. Then 0395.5 selects subtraction when set or addition when clear,
using unsigned byte 0398 and 16-bit wrapping. The three service-bit tests are
separate samples of the raw byte.

Regardless of service admission, write the result to 01EE and then 01F0.
There is **no re-clamp after service edits**: this path can deliberately leave
the earlier signed limits. Neither RAM store is an actuator transaction or a
period/EST conversion.

## Calibration and failure prefixes

| Source | Stock value | Profile ownership |
|---|---|---|
| 4132 | 0B | `spark.reference_bias` |
| 4E90 | 01 | `spark.override_options` |
| 4161,4162,4164,4165 | FF,0000,00,00 | Override coolant, command, entry TPS and retained TPS |
| 4144 | 0077 | `spark.upper_limit` |
| 4146,4148,414A,414C | FFF5,FFF5,FFF5,0000 | Normal, recovery and two transmission floors |
| 48DA | 06 | Existing shared `reference.throttle_limit`; no duplicate calibration field |
| 400F,45D8..45DA,46DF..46E2,4E77 | Existing values | Prior/shared knock calibration |

This introduces 17 distinct calibration bytes. The command suite verifies 27
stock bytes including 10 prior/shared bytes; the expanded spark fixture exports
1,162 distinct bytes across its participating profiles. Runtime calibration
descriptors remain independent of the future serialized memory layout.

Missing calibration/profile returns `PCM_BAD_CONFIGURATION` from the override
or limit routines. The inactive extension and service/common-commit routines
need neither calibration nor hardware. Wrappers preserve all successful earlier
writes on failure. A missing extension prevents reference subtraction and
observation consumption. Failure at SEI preserves pending observations; failure
at CLI follows their consumption and leaves the mask set. These error returns
are development contracts, not new error-return instructions in the factory ROM.

## Verification and remaining work

The new suite compares 356,872 compiled-C results against actual ROM instructions:
66,124 upper/reference cases, 73,280 lower/selector cases, 16,640 override cases,
132,352 service/common-latch cases, 65,536 ordered command cases, two burst
arm/expiry witnesses, 96 explicit extension witnesses, 2,048 calibration/state
variants, 512 composite→command witnesses, 90 mask/extension failure prefixes
and 192 retained-state history calls. All 137 instruction starts in A9E0..AB43
execute. The suite checks RAM state, ordered mask/task events, final mask and
unresolved dependency, rejects hardware I/O in these scopes, and checks local
ROM stack balance on completed calls.

Every 16-bit input is covered in the upper, normal-floor, service and command
corpora with selected bound/profile patterns. Directed signed-overflow/equality
edges, every transmission-status byte, every service flag/amount pair,
override hysteresis and enabled/disabled option variants supplement those
corpora. This is not an exhaustive product of all states or interrupt
interleavings; target C stack costs, compiler ABI and timing remain separate.

Both host verification routes retain this command suite and the newer admission
contracts/differential checks, bringing CTest to 20 entries. The source inventory
is 122 public routines: 51 implemented outlines, 40 explicit dependency boundaries
and 31 implemented algorithms. These counts are not whole-firmware equivalence.
The [A466..A5E4 admission prelude](spark_admission_contract.md) is now callable.
Next source work is A5E5..A6FF period/RPM preparation and the AB44 period/EST
conversion/output path, with unfinished producers and the optional module
remaining explicit.

See the [modifier contract](spark_modifiers_contract.md),
[knock contract](knock_control_contract.md),
[upstream derivation](../../docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md)
and [integer handoff](../../docs/analysis/FACTORY_SPARK_INTEGER_HANDOFF.md).
