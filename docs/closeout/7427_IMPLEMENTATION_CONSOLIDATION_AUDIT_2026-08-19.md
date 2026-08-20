# 7427 Implementation Consolidation Audit — 2026-08-19

## Status

```text
AUDITED / CONSOLIDATED ON BRANCH
branch: audit/consolidate-2026-08-19
main: untouched
```

This audit reconciles the ROM-first implementation branch with the separate spark ALDL/KR proof branch, removes obsolete/duplicate project-state artifacts, and establishes one current implementation frontier.

## 1. Branch state

Branches at audit start:

```text
main
agent/rom-first-bootstrap
docs/spark-aldl-kr-ordering-proof
```

Starting relationships:

```text
agent/rom-first-bootstrap
  30 commits ahead of main
  0 behind

docs/spark-aldl-kr-ordering-proof
  1 commit ahead of main
  0 behind
```

Consolidation branch:

```text
audit/consolidate-2026-08-19
```

It was created from `agent/rom-first-bootstrap`. No merge to `main` and no branch deletion is part of this audit.

## 2. Canonical authority after consolidation

Current implementation/project-state authority:

```text
docs/WORKING_STATE.md
docs/closeout/7427_IMPLEMENTATION_CONSOLIDATION_AUDIT_2026-08-19.md
docs/closeout/7427_COMPLETION_STATUS.md
docs/implementation/ROM_FIRST_BUILD_PATH.md
docs/implementation/ASM11_MINIIDE_BUILD.md
```

Frozen V1 semantic-planning authority:

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

Stock/hardware evidence:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
docs/contracts/*.md
maps/contracts/*.csv
```

The 2026-08-13 planning audit remains semantic authority. Its old implementation-next-step section is historical and is superseded by the current working-state/implementation documents.

## 3. Actual implementation frontier

### Milestone A — reset/bootstrap/vector image

```text
classification: PROVEN BUILD
source: source/replacement_os/7427_bootstrap_miniide.asm
assembler: ASM11 V1.26 Build 144
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

### Milestone B — read-only ADC/REF-period acquisition image

```text
classification: PROVEN BUILD
live hardware input proof: PENDING
source: source/replacement_os/7427_inputs_miniide.asm
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

Important boundary:

```text
$3FC0 read = build-proven
$3FC0 as meaningful live REF/DRP data = NOT YET replacement-image bench-proven
```

Stock firmware initializes the `$3FC0-$3FFA` ASIC/register island. Milestone B intentionally omits broad stock ASIC/output initialization, so the minimum read-only-safe initialization required for meaningful REF/cranking data remains unresolved.

### Milestone C — engine-off SCI/ALDL observability

```text
classification: SOURCE IMPLEMENTED
assembly/listing proof: PENDING
S19/BIN proof: PENDING
bench proof: PENDING
source: source/replacement_os/7427_aldl_tx_miniide.asm
```

Implemented source behavior:

```text
8192-baud SCI
14-byte raw-input telemetry frame
SCI interrupt TX service
stock BMHM/TBI $3FFC/$3FFD = $B93A baseline
ALDL external-driver control on low-byte $3FFD bit2
no injector writes
no spark/EST writes
no IAC writes
no pump writes
no auxiliary-output writes
```

The immediate implementation gate is Milestone-C ASM11/listing/S19/BIN proof, followed by engine-off PCM bench observation.

## 4. Source-role consolidation

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
7427_bootstrap_miniide.asm   Milestone A
7427_inputs_miniide.asm      Milestone B
7427_aldl_tx_miniide.asm     Milestone C
```

Flattened convenience source:

```text
source/replacement_os/7427_rom_miniide.asm
```

The `*_miniide.asm` stages intentionally remove include-path/tooling friction. They remain useful proof vehicles, but verified behavior must be folded into the modular source rather than allowing permanent source drift.

## 5. Status contradictions corrected

The following files previously disagreed about the current frontier:

```text
README.md
  described assembler/baseline ROM work as future work despite proven A/B builds

docs/WORKING_STATE.md
  recognized Milestone A but still listed Milestone B build/listing as pending

docs/closeout/7427_COMPLETION_STATUS.md
  claimed successful ASM11 assembly/listing had not yet occurred

docs/implementation/ASM11_MINIIDE_BUILD.md
  documented A proof but omitted already-proven B
docs/implementation/ROM_FIRST_BUILD_PATH.md
  described sequence without the current A/B/C checkpoint
```

They now agree:

```text
A = proven build
B = proven build; live hardware acquisition still pending
C = implemented source; assembly/bench proof pending
```

`docs/implementation/ASM11_BOOTSTRAP_PROOF.md` is retained as the Milestone-A proof but now explicitly points current-work questions to `WORKING_STATE.md` instead of calling Milestone B the next gate.

## 6. Hardware corrections/contracts retained

ADC/register identity:

```text
$3008 = relocated CPU PORTD / external ADC-mux selector
$3039 = relocated HC11 OPTION
```

ALDL board baseline:

```text
$3FFC/$3FFD = $B93A
```

before normal BMHM/TBI serial activity.

Distinct bit-2 controls:

```text
$3FFD bit2 = ALDL external-driver control, low byte
$3FFC bit2 = async-fuel-related control, high byte
```

Authority:

```text
docs/contracts/ALDL_SCI_HANDSHAKE.md
```

## 7. Spark ALDL / knock-retard proof consolidated

Added to the consolidation branch:

```text
docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md
```

Locked normal `$31` interpretation:

```text
ALDL Spark Advance = post-normal-KR spark value
ALDL Knock Retard  = amount removed by normal knock logic
```

Do not subtract KR from logged Spark Advance again.

Static proof chain:

```text
L01FD
-> L01EE
-> L020C normal KR
-> LSRA converts KR 256/45 -> 256/90 scale
-> KR subtraction from L01EE at $AAD1-$AAD8
-> post-KR L01EE copied to L01F0 at $AB3E-$AB41
-> ALDL pointer $31F0 masked/dereferenced as live $01F0
```

Approximate pre-KR demand:

```text
logged Spark Advance + logged Knock Retard
```

subject to serialized ALDL sampling skew.

## 8. Obsolete/duplicate files removed

Removed because they were stale snapshots, exact duplicates, or superseded pre-ROM-first authority:

```text
docs/FILE_MANIFEST.md
  obsolete file-size/list snapshot

docs/REPO_COMMIT_MANIFEST.md
  obsolete v0.2 prepared-file snapshot

docs/7427_Calibration_Layout_v0.1.md
docs/CALIBRATION_LAYOUT.md
  exact duplicate pair; superseded pre-ROM-first calibration layout

docs/7427_Minimal_OS_Skeleton_v0.1.md
docs/MINIMAL_OS_SKELETON.md
  exact duplicate pair; superseded fixed-memory OS skeleton

docs/7427_Static_Analysis_Summary_v0.2.md
  superseded by stable v0.3 summary

docs/implementation/ASM11_BOOTSTRAP_RESULT.md
  duplicate of the stronger ASM11_BOOTSTRAP_PROOF.md evidence
```

Git history remains the archive.

Kept:

```text
docs/STATIC_ANALYSIS_SUMMARY.md v0.3
current contracts/planning authorities
bench/test evidence
Milestone A/B/C sources
modular replacement-OS source
```

The v0.3 static summary now carries an explicit historical-evidence notice so its old priority list cannot be mistaken for the current work order.

## 9. CI/verifier audit

`.github/workflows/rom-bootstrap-verification.yml` previously ran push verification only on `agent/rom-first-bootstrap`. That branch-specific push restriction was removed; source/verifier changes now trigger the structural workflow on any branch.

`tools/verify_rom_bootstrap.py` remains a structural check of the maintainable modular source, covering:

```text
fixed placement anchors
low-RAM allocation below stack
32 vectors $FFC0-$FFFE
external reset -> RESET_ENTRY
no production-output commit calls from first modular master
$3008 PORTD ADC-mux identity
$3039 OPTION offset
```

Its header now states explicitly that it complements ASM11 listing/S19/BIN proof and bench validation rather than replacing them.

## 10. Unresolved implementation items

```text
Milestone-C ASM11/listing/S19/BIN proof
Milestone-C engine-off bench proof
live ADC acquisition proof
minimum safe ASIC initialization for meaningful REF/cranking observability
fold proven B/C behavior into modular ROM master
engineering ADC -> VDC -> engineering transfer pipeline
sensor filtering / validity / substitution
configurable REF geometry / RPM scaling / TDC offset
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
1. assemble 7427_aldl_tx_miniide.asm with proven ASM11 V1.26
2. inspect listing, RAM, code end, vectors, SCI ISR and absolute hardware addresses
3. checksum-validate S19 and convert to deterministic 64 KiB BIN
4. bench-run Milestone C engine-off and verify frame + ALDL-driver release
5. verify actual ADC values on the PCM
6. establish minimum safe ASIC startup for useful REF/cranking data
7. fold proven B/C behavior into modular ROM master/HAL/core
8. implement engineering sensor pipeline and configurable REF geometry
9. complete full spark/EST preserved rolling-state handoff
10. implement engine-running modules in frozen semantic-interface order
11. generate XDF/ADX from actual built layouts
```

## 12. Branch disposition recommendation

After this consolidation branch is reviewed and merged:

```text
audit/consolidate-2026-08-19
  merge candidate for main

agent/rom-first-bootstrap
  superseded after merge

docs/spark-aldl-kr-ordering-proof
  superseded after merge

main
  remains untouched until explicit merge authorization
```

Do not delete superseded branches until the consolidation is safely merged and the resulting `main` state is verified.
