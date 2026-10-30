# Source evidence and historical prototypes

The active modular replacement-firmware source is
[pseudo-source/](../pseudo-source/README.md). It has its own interfaces,
calibration definitions, host checks and unfinished target-backend boundaries.

## Stock evidence

`source/31/BMHM_HAC_ORG_7100_to_end.asm` is the preserved original listing.
Actual hash-identified BMHM ROM bytes and the reviewed rooted overlays take
precedence over conflicting labels, data declarations or operands in that
listing. Do not rewrite the original evidence to hide those discrepancies.

Stock BMHM SHA-256:

```text
6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

The broader[raw-source trace](../maps/source_trace/README.md) preserves
calibration/data provenance. Unknown scales and inherited names remain
candidate metadata rather than verified engineering units.

## Current truck calibration

The user reports restoring the regular 0.3.12 tune. Its exact normal-image
filename and SHA-256 are not asserted here. The old `2.bin` snapshot and its
hash are historical. Use[WORKING_STATE.md](../docs/WORKING_STATE.md) and the
exact current image for byte-specific tuning facts.

## Retained prototypes

[replacement_os/](replacement_os/README.md) and
[minimal_os/](minimal_os/README.md) preserve earlier assembly and output-slice
proofs. They are separate implementations with their own build/bench scope.
They remain useful reference and regression material; their original memory
layout or next-step wording does not constrain the new C source.
