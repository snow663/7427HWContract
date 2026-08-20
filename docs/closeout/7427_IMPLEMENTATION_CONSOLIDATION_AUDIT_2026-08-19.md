# 7427 Implementation Consolidation Audit — 2026-08-19

## Status

```text
AUDITED / CONSOLIDATED ON BRANCH
branch: audit/consolidate-2026-08-19
main: untouched
```

This audit reconciles the implementation work that accumulated on `agent/rom-first-bootstrap` with the separate spark ALDL/KR proof branch. It establishes the current implementation frontier, removes stale duplicate planning snapshots, and separates proven build facts from source-only and bench-pending claims.

## 1. Branches at audit start

```text
main
agent/rom-first-bootstrap
docs/spark-aldl-kr-ordering-proof
```

At audit start:

```text
agent/rom-first-bootstrap
  30 commits ahead of main
  0 behind main

 docs/spark-aldl-kr-ordering-proof
  1 commit ahead of main
  0 behind main
```

The consolidation branch was created from `agent/rom-first-bootstrap`:

```text
audit/consolidate-2026-08-19
```

No merge to `main` and no branch deletion is part of this audit.

## 2. Canonical authority split after consolidation

### Current implementation / project-state authority

```text
docs/WORKING_STATE.md
docs/closeout/7427_IMPLEMENTATION_CONSOLIDATION_AUDIT_2026-08-19.md
docs/closeout/7427_COMPLETION_STATUS.md
docs/implementation/ROM_FIRST_BUILD_PATH.md
docs/implementation/ASM11_MINIIDE_BUILD.md
```

### Frozen semantic-planning authority

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
docs/planning/V1_*.md
maps/planning/v1_configuration_variables.csv
maps/planning/v1_module_interface_matrix.csv
maps/planning/v1_calibration_manifest.csv
maps/planning/v1_table_geometry.csv
maps/planning/v1_degraded_operation_policy.csv
maps/telemetry/v1_adx_manifest.csv
```

The 2026-08-13 planning audit remains authoritative for V1 semantics. Its historical implementation-next-step section predates the ROM-first bootstrap work and is superseded by the current implementation/status documents above.

### Hardware / stock-behavior evidence

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
docs/contracts/*.md
maps/contracts/*.csv
```

Current contracts are allowed to refine older static summaries when a later trace proves a more specific behavior.

## 3. Actual implementation frontier

### Milestone A — reset/bootstrap/vector image

Classification:

```text
PROVEN BUILD
```

Source:

```text
source/replacement_os/7427_bootstrap_miniide.asm
```

Observed/proven:

```text
assembler: ASM11 V1.26 Build 144 for WIN32 (x86)
warnings: 0
errors: 0
RESET_ENTRY: $7100
executable: $7100-$7136
vectors: $FFC0-$FFFF
external reset: $FFFE -> $7100
64 KiB BIN SHA256:
c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

Proof authority:

```text
docs/implementation/ASM11_BOOTSTRAP_PROOF.md
```

### Milestone B — read-only ADC / REF-period acquisition image

Classification:

```text
PROVEN BUILD
LIVE HARDWARE INPUT PROOF STILL PENDING
```

Source:

```text
source/replacement_os/7427_inputs_miniide.asm
```

Observed/proven:

```text
assembler: ASM11 V1.26 Build 144
warnings: 0
errors: 0
RAM: $0000-$0009
RAM_ALLOC_END: $000A
executable: $7100-$71D7
ROM_CODE_END: $71D8
vectors: $FFC0-$FFFF
external reset: $FFFE -> $7100
64 KiB BIN SHA256:
28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

Proof authority:

```text
docs/implementation/MILESTONE_B_BUILD_PROOF.md
```

Important interpretation boundary:

```text
$3FC0 read exists and is build-proven.
$3FC0 as meaningful live REF/DRP data is NOT yet replacement-image bench-proven.
```

Stock firmware performs initialization in the `$3FC0-$3FFA` ASIC/register island. Milestone B deliberately omits broad stock ASIC/output initialization, so the minimum read-only-safe initialization required for meaningful REF/cranking data remains a bench/static target.

### Milestone C — engine-off SCI/ALDL observability image

Classification:

```text
SOURCE IMPLEMENTED
ASSEMBLY/LISTING PROOF PENDING
S19/BIN PROOF PENDING
BENCH PROOF PENDING
```

Source:

```text
source/replacement_os/7427_aldl_tx_miniide.asm
```

Implemented source behavior:

```text
8192-baud SCI
14-byte raw-input telemetry frame
SCI interrupt TX service
stock BMHM/TBI $3FFC/$3FFD = $B93A board-control baseline
ALDL external-driver control on low-byte $3FFD bit2
no injector writes
no spark/EST writes
no IAC writes
no pump writes
no auxiliary-output writes
```

The immediate implementation gate is Milestone-C ASM11/listing/S19/BIN proof followed by engine-off PCM bench observation.

## 4. Maintainable source vs proof-stage source

Long-term maintainable source authority:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/*.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
source/replacement_os/hal/*.inc
```

Self-contained proof-stage sources:

```text
source/replacement_os/7427_bootstrap_miniide.asm   Milestone A
source/replacement_os/7427_inputs_miniide.asm      Milestone B
source/replacement_os/7427_aldl_tx_miniide.asm     Milestone C
```

Flattened convenience source:

```text
source/replacement_os/7427_rom_miniide.asm
```

The `*_miniide.asm` stages intentionally remove include-path/tooling friction. They are useful proof vehicles, but verified behavior must be folded into the modular source instead of allowing permanent source drift.

## 5. Status contradictions corrected

Before this audit, the top-level documents disagreed about the implementation frontier.

Corrected contradictions included:

```text
README.md
  previously described assembler/toolchain/baseline ROM assembly as future work
  despite proven Milestone A and B builds.

docs/WORKING_STATE.md
  knew Milestone A was proven but still listed Milestone B build/listing as pending.

docs/closeout/7427_COMPLETION_STATUS.md
  still claimed no successful ASM11 assembly/listing proof existed.

docs/implementation/ASM11_MINIIDE_BUILD.md
  documented Milestone A proof but omitted the already-proven Milestone B result.

docs/implementation/ROM_FIRST_BUILD_PATH.md
  described the historical sequence but did not state the current A/B/C checkpoint.
```

All five now agree on:

```text
A = proven build
B = proven build, live hardware acquisition still pending
C = implemented source, assembly/bench proof pending
```

## 6. Hardware/semantic corrections retained

### ADC register identity

Current proven interpretation:

```text
$3008 = relocated CPU PORTD / external ADC-mux selector
$3039 = relocated HC11 OPTION register
```

The earlier `$3008 = OPTION` interpretation is superseded.

### ALDL board-control baseline

Stock BMHM/TBI startup establishes:

```text
$3FFC/$3FFD = $B93A
```

before normal serial activity.

The replacement ALDL bring-up must establish this known baseline before read/modify/write of the pair. The two bit-2 controls are distinct:

```text
$3FFD bit2 = ALDL external-driver control, low byte
$3FFC bit2 = async-fuel-related control, high byte
```

Authority:

```text
docs/contracts/ALDL_SCI_HANDSHAKE.md
```

## 7. Spark ALDL / knock-retard proof consolidated

The separate proof branch was folded into this consolidation branch as:

```text
docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md
```

Locked interpretation for normal `$31` operation:

```text
ALDL Spark Advance = post-normal-KR spark value
ALDL Knock Retard  = diagnostic amount removed by normal knock logic
```

Do not subtract KR from logged Spark Advance again.

Static proof chain:

```text
L01FD
 -> L01EE
 -> normal KR stored at L020C
 -> LSRA converts KR from 256/45 to 256/90 scale
 -> KR explicitly subtracted from L01EE at $AAD1-$AAD8
 -> post-KR L01EE copied to L01F0 at $AB3E-$AB41
 -> ALDL pointer $31F0 is masked/dereferenced as live RAM $01F0
```

Approximate pre-KR demand may be reconstructed as:

```text
logged Spark Advance + logged Knock Retard
```

subject to serialized ALDL sampling skew. The prior idle timing-light comparison had KR=0 and therefore validates display/scaling at that condition, not KR ordering; ordering comes from the code trace.

## 8. Removed obsolete / duplicate files

The following files were removed from the consolidation branch because they were exact duplicates, stale snapshots, or contradicted the current ROM-first authority model:

```text
docs/FILE_MANIFEST.md
  obsolete static file-size/list snapshot

docs/REPO_COMMIT_MANIFEST.md
  obsolete v0.2 prepared-file snapshot

docs/7427_Calibration_Layout_v0.1.md
docs/CALIBRATION_LAYOUT.md
  exact duplicate pair; obsolete pre-ROM-first calibration layout

docs/7427_Minimal_OS_Skeleton_v0.1.md
docs/MINIMAL_OS_SKELETON.md
  exact duplicate pair; obsolete fixed direct-page/subsystem allocation skeleton

docs/7427_Static_Analysis_Summary_v0.2.md
  superseded by docs/STATIC_ANALYSIS_SUMMARY.md v0.3
```

Git history remains the archive for these removed artifacts.

No current hardware contracts, planning authorities, bench evidence, Milestone A/B/C proof source, or stable v0.3 static summary was removed.

## 9. CI / verifier audit

### Workflow

`.github/workflows/rom-bootstrap-verification.yml` previously ran push verification only on:

```text
agent/rom-first-bootstrap
```

That branch-specific restriction was removed. Source/verifier changes now trigger the structural verification workflow regardless of branch, while PR and manual triggers remain.

### Structural verifier

`tools/verify_rom_bootstrap.py` remains intentionally narrower than ASM11 and bench proof. It checks the maintainable modular source for:

```text
fixed placement anchors
low-RAM allocation below stack
32 vectors from $FFC0-$FFFE
external reset -> RESET_ENTRY
absence of production-output commit calls in first modular master
$3008 PORTD ADC-mux identity
$3039 OPTION offset
```

Its documentation now explicitly states that it complements, rather than replaces, ASM11 listing/S19/BIN proof and bench validation.

## 10. Current unresolved implementation items

```text
Milestone-C ASM11/listing/S19/BIN proof
engine-off Milestone-C bench proof
live ADC acquisition proof on the PCM
minimum safe ASIC initialization for meaningful REF/cranking observability
fold proven B/C behavior into modular ROM master
engineering ADC -> VDC -> engineering transfer pipeline
sensor filtering / validity / substitution
configurable REF event count, RPM scaling and TDC offset
hybrid SD/Alpha-N air-charge manager
mass-based fuel / injector model
spark / idle / knock control algorithms
full spark/EST rolling-state preserved island
production telemetry packet/page
calibration ROM objects
actual XDF
actual production ADX
```

## 11. Correct next work order

```text
1. assemble source/replacement_os/7427_aldl_tx_miniide.asm with proven ASM11 V1.26
2. inspect listing, RAM allocation, code end, vectors, SCI ISR and absolute hardware addresses
3. checksum-validate S19 and convert to deterministic 64 KiB BIN
4. bench-run Milestone C engine-off and verify frame data and ALDL-driver release
5. verify actual ADC values on the PCM
6. establish the minimum safe ASIC startup required for useful REF/cranking data
7. fold proven Milestone B/C behavior into source/replacement_os/7427_rom.asm and modular HAL/core
8. implement engineering sensor pipeline and configurable REF geometry
9. complete the full spark/EST preserved rolling-state handoff
10. implement engine-running modules in frozen semantic-interface order
11. generate/maintain XDF and ADX from actual built layouts
```

## 12. Branch disposition recommendation

After review/merge of this consolidation branch:

```text
audit/consolidate-2026-08-19
  -> merge candidate for main

agent/rom-first-bootstrap
  -> superseded by consolidation branch after merge

docs/spark-aldl-kr-ordering-proof
  -> superseded by consolidation branch after merge

main
  -> remains untouched until explicit merge authorization
```

Do not delete the two superseded branches before the consolidation branch is safely merged and the resulting `main` state is verified.
