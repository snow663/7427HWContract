# 7427HWContract

GM16197427 / $31 PCM hardware contracts, stock BMHM reverse engineering,
modular replacement-firmware source, ROM simulation and tuning references.

[Working state](docs/WORKING_STATE.md) is the single live project-state index.
Older investigations and prototype build records retain their original scope.

## Current work

| Workstream | Start here | Status |
|---|---|---|
| Modular C replacement firmware | [pseudo-source/](pseudo-source/README.md) | 141 public routine files; checked kernel/reset/REF/spark logic, fixed-point algorithms and explicit unfinished bodies |
| Factory behavior and hardware | [Ownership closure](docs/analysis/FACTORY_OWNERSHIP_CLOSURE.md) | ROM-backed access, arithmetic, state and interface contracts |
| Timing and interrupts | [Timing closure](docs/analysis/FACTORY_INTERRUPT_AND_TIMING_CLOSURE.md) | Conditional source/deadline/stack contracts; physical premises remain explicit |
| Remaining information | [Equivalence ledger](docs/analysis/FACTORY_EQUIVALENCE_INFORMATION_GAPS.md) | Scoped specifications plus identified ROM/device/board/module work |
| Truck tuning | [Runtime workflow](docs/TRUCK_FIRST_RUNTIME_DECODING.md) | Use the exact current tune and matching logs for calibration-specific conclusions |
| ROM simulator | [hac31_romsim/](hac31_romsim/README.md) | Existing clickable GUI and instruction/peripheral fixtures |

The user restored the **regular 0.3.12 tune** after the temporary 1800 readback
probe. Its exact normal-image filename and SHA-256 are not asserted here.
The old `2.bin` snapshot is historical and is not the current calibration
value authority. No old pressure, injector, VSS or table value is promoted to
current tune fact without checking the current image and observations.

## Evidence authority

Stock BMHM SHA-256:

```text
6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

Actual hash-identified ROM bytes take precedence over conflicting HAC labels.
The original listing remains preserved in
[source/31/](source/README.md); mapped 4000..FFFF evidence is committed in
[maps/structure/](maps/README.md). BIN padding below 4000 is not runtime RAM.
Source-only maps are useful indexes, not stronger evidence than rooted,
ROM-checked access and state contracts.

The test probe returned a checksum-valid 24-byte all-zero sample from actual
CPU 1800..1817. [The observation](pseudo-source/reference/1800_readback.md)
records its image identity and limits. It does not prove RAM backing or
writability, and the optional module/loader is outside the initial C scope.

## Verification

```sh
python -m unittest discover -s tests -p 'test_factory_*.py' -v
python pseudo-source/tests/run_checks.py
python tools/verify_repository_hygiene.py
```

From `hac31_romsim/`, run `python -m unittest discover -s tests -v`.

The current C work is a host-compilable source outline, not a target image
build. Its implemented kernel checks and 532 compiled-C base-fuel/ROM cases
are joined by 128 startup and 4,112 REF transaction comparisons plus 64 injected
I/O-failure positions. The full REF body adds 2,502 handler comparisons, 143 failure
prefixes and 38 direct timer-entry cases. These remain separate from the 190
factory tests. OC1 adds 261,632 numeric comparisons, 16 I/O-failure cases and 1,280
REF/OC1 sequences. The target hardware backend,
startup/vector assembly, final linker/calibration layout and HC11 cycle/stack
checks remain next work. [CMake instructions](pseudo-source/README.md) are
also available and checked in CI.

## Historical and retained material

- [Earlier assembly prototypes](source/replacement_os/README.md) preserve
  bootstrap/read-only/debug proofs; they are separate from the active C source.
- [Earlier minimal output slices](source/minimal_os/README.md) retain their
  original source/bench limitations.
- [Frozen V1 design](docs/planning/README.md) and
  [planning maps](maps/planning/README.md) are optional reference inputs.
- [Dated investigations](docs/investigations/README.md) describe the image/log
  snapshot named in each document.
- [Closeout records](docs/closeout/README.md) are historical checkpoints.

[Repository audit](docs/REPOSITORY_AUDIT.md) explains the current cleanup,
retired exports and validation. Git history preserves removed artifacts;
we keep the original source, required generated evidence and useful proofs.
