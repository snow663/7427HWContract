# Truck runtime and tuning workflow

This workflow supports the current running tune using the factory contracts.
The active firmware source is [pseudo-source/](../pseudo-source/README.md);
the exact current project state is indexed in [WORKING_STATE.md](WORKING_STATE.md).

## Establish the image and observations

The user restored the regular 0.3.12 tune after the1800 readback probe. Its exact
normal-image filename/SHA-256 are not asserted here. A saved test/probe image
must not be substituted for that normal image. Historical `2.bin` and dated
logs remain comparisons, not current calibration-value authority.

For a tuning task, identify the exact current BIN, relevant matching logs and
actual present settings. Read calibration values from that image. Keep reported
symptoms, sampled/logged values and inferred internal state distinguishable.
Old pressure, injector, timing, VSS and learned-state assumptions need current
confirmation when they affect the conclusion.

## Trace through the factory contracts

Stock BMHM bytes establish the reference algorithm, integer arithmetic,
admission and hardware transaction order. They do not establish the current
modified tune's values or prove every patch preserves the stock control path.
Use the[engine closure](analysis/FACTORY_ENGINE_CALCULATION_CLOSURE.md),
[idle/speed closure](analysis/FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md), and
[serial protocol](analysis/FACTORY_SERIAL_ALDL_PROTOCOL.md) as starting points.

ALDL serializes live fields; one host row is not an atomic snapshot. The later
[VSS transport reassessment](investigations/VSS_FUELING_TRANSPORT_REASSESSMENT_2026-08-20.md)
supersedes the old inference about exact VSS/BPW order from adjacent rows.
The historical `2.bin` VSS consumer audit does not establish which consumers
remain active in the current0.3.12 tune.

Preserve the distinction between BLM's multiplicative correction and INT/P's
signed additive correction. Spark plus normal KR reconstructs an approximate
pre-normal-KR demand, with upstream modifiers and serialization skew retained;
it is not automatically the raw main-table value.

## Capture reusable findings

Record materially decoded behavior with its image/log identity and evidence
level: ROM-byte checked, calibration-byte checked, replay validated, physical
observation, or inference. A physical readback establishes only the returned
values under the observed condition. Keep unknown scaling and hardware effects
explicit instead of copying inherited labels into new authority.

Use controlled, attributable changes for tuning. The modular C source can reuse
these hardware/algorithm contracts while adopting a different feature set,
calibration layout and algorithms. Tuning the running stock-derived image and
building replacement firmware remain separate implementations.
