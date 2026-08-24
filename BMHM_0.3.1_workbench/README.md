# BMHM 0.3.1 workbench

This folder is intentionally separate from the canonical project contracts and source maps.

It captures the experimental truck calibration state reached on 2026-08-23, the source-level traces used to justify it, and the validation notes from the logs used while developing it.

## Current image

- Generated artifact: `BMHM_0.3.1.bin` (binary is not duplicated in this documentation branch)
- Size: 65536 bytes
- SHA-256: `da9898b1f1342fe4b23f379ed7057916b141f5550c4b5b0f80a11771b4aa34a1`
- `$31` checksum at `$4006-$4007`: `$216C`
- Base calibration lineage: `2.1.bin` (spark-edited `2.bin`)
- Closed-loop DAMP1 calibration: included
- repaired open-loop-idle hook/toggle: included
- global closed-loop-fueling bypass toggle: included
- consumer-level VSS authority removal: included
- true-idle RPM gate: included

## Folder contents

- `mods/BMHM_0.3.1_PATCH_NOTES.md` — byte/address-level modification history and current BIN identity.
- `mods/TUNERPRO_PARAMETERS.md` — flags and scalars needed in the XDF.
- `reverse_engineering/SOURCE_TRACE_2026-08-23.md` — decoded stock `$31` behavior used today.
- `reverse_engineering/TPS_SELF_ZERO_TRACE.md` — TPS A/D -> learned zero -> engine TPS path and remaining VSS coupling.
- `validation/CLOSED_LOOP_DAMP1_2026-08-23.md` — current closed-loop performance check against the pre-DAMP1 reference log.

## Important status

`BMHM_0.3.1.bin` is an experimental truck calibration, not stock authority.

The rejected experiment that forced VSS RAM values to zero is **not** part of this image. VSS acquisition/filtering remains stock so phantom speed remains visible in ALDL; authority is removed at engine-control consumers instead.

The TPS self-zero trace found one remaining indirect VSS dependency in the TPS offset learner. It is documented but not patched in 0.3.1.
