# Source Inputs

## Stock `$31` executable-side source authority

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

Metadata:

```text
mask: $31
bin/object: BMHM
processor: MC68HC11-family
register relocation: INIT -> $30, HC11 regs at $3000
analysis base: ORG $7100 through vector/end region
```

Use this committed source for static algorithm ordering, RAM dataflow, scheduler/state logic, ALDL behavior, and hardware-interface proof.

## Current truck calibration authority

The truck is currently running:

```text
2.bin
SHA-256: 2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

`2.bin` is the current calibration-byte/table/threshold authority for road-log and tuning analysis. Do not assume stock BMHM calibration values are still present in the running truck.

The numbered BIN is an external reference artifact unless explicitly committed later.

## Broader raw-source trace

Provenance for the supplied broader HAC source-derived ORG/data trace package is recorded at:

```text
maps/source_trace/README.md
```

Source-derived trace rows are evidence/index material; unknown scaling remains unknown until independently proven.