# 7427HWContract

Working repository for the GM 16197427 `7427` PCM hardware-contract reverse-engineering and replacement-OS project.

The repo is the project state. Git history is the version record. Exported ZIPs/CSVs are not the primary working record.

## Objective

Build a clean engine-control OS for the `7427` using the stock `$31` BMHM/HAC executable as the software/hardware authority where appropriate.

V1 engine-control scope includes:

- speed-density TBI fuel
- bounded Alpha-N air-charge assistance/fallback
- spark control
- IAC/idle air control
- AE / PE / DFCO
- crank / warmup / afterstart fuel
- injector low-pulsewidth transfer correction
- NB/WB oxygen feedback
- knock handling
- ALDL/debug visibility

Out of V1 scope unless hardware-required:

- automatic transmission strategy
- TCC strategy
- EGR
- EVAP/purge
- secondary AIR
- A/C compressor/idle-up strategy
- inherited GM mode-word baggage

Unused I/O remains documented/reserved for later expansion.

## Current architecture

```text
CALIBRATION / XDF
        ↓
ENGINEERING-UNIT INPUT + CONTROL SYSTEM
        ↓
SEMANTIC REQUESTS / ARBITRATION
        ↓
PRESERVED GM COMMAND ISLANDS + HAL
        ↓
7427 HARDWARE
```

The first-running-engine route preserves source-proven GM software-to-hardware command behavior. Complete electrical characterization of every retained output is not a prerequisite when its complete stock command island is preserved.

## Current status

Frozen reverse engineering:

```text
algorithm extraction             100%
scheduler/lifecycle extraction   100%
diagnostics/failsafe extraction  100%
production calibration audit     100%
V1 software-facing HW contract   100%
physical endpoint confirmation     0% intentionally deferred
```

Frozen V1 semantic planning:

```text
feature scope                     100%
control/formula semantics         100%
physical/setup model              100%
sensor transfer model             100%
signal conditioning               100%
rotation/reference geometry        100% for validated V1 relationship
module interfaces                 100%
calibration semantic exposure     100%
calibration table geometry        100%
telemetry semantic channels       100%
degraded-operation policy         100%
```

Implementation:

```text
replacement-OS implementation    ~19%
complete engine-running image      0%
```

The project has crossed from broad reverse engineering/planning into **ROM implementation**.

## ROM-first implementation rule

The executable image is the placement authority.

We do **not** freeze a complete RAM partition, complete fixed-point matrix, XDF address map, or ADX packet map before the code exists.

```text
hardware-proven boundaries
        ↓
build replacement ROM
        ↓
allocate RAM/calibration objects as real modules require them
        ↓
verify assembly/binary map
        ↓
XDF describes actual calibration layout
        ↓
ADX describes actual telemetry packet layout
```

Frozen semantic units and table geometry remain design authority. Exact storage representation and address become fixed when implementation creates the object.

Implementation-order authority:

- `docs/implementation/ROM_FIRST_BUILD_PATH.md`
- `docs/WORKING_STATE.md`

## First replacement ROM master

Current master source:

```text
source/replacement_os/7427_rom.asm
```

Current stock-proven placement anchors:

```text
low runtime RAM begins       $0000
stock stack top              $03FF
additional stock-used RAM    $0800-$08FF
HC11 reset register base     $1000
HC11 relocated register base $3000
stock calibration/header     $4000+
first replacement code ORG   $7100
HC11 vector window           $FFC0-$FFFF
external reset vector        $FFFE
```

The first master currently:

- enters through the real external reset vector
- sets the stock stack top
- relocates HC11 registers `$1000 -> $3000`
- applies the source-proven CPU-side reset configuration
- clears only RAM allocated by the current build
- initializes semantic state with every actuator permission disabled
- initializes IAC software state without commanding the IAC output
- services the COP in a stable engine-off loop
- sends every unowned interrupt/vector to a COP-serviced safe halt
- links existing command-island source without calling production-output commit routines

It is not yet an engine-running image.

## Preserved output islands

```text
fuel synchronous   LOCKED + PORTED
fuel async / AE    LOCKED + PORTED
IAC                LOCKED + PORTED
fuel pump          LOCKED + PORTED
spark / EST        ABI LOCKED; complete rolling-state port pending
MIL                deferred
unused I/O         reserved
```

Authority:

- `docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md`
- `source/replacement_os/hal/gm_output_islands.asm`

Current first-image permissions remain:

```text
fuel  = FALSE
spark = FALSE
IAC   = FALSE
pump  = FALSE
aux   = FALSE
```

## ADC evidence correction found during ROM bootstrap

The earlier ADC HAL called `$3008` `HC11_OPTION`.

Stock routine `F275` proves `$3008` is relocated CPU PORTD and that bits 3..5 are used as the external ADC/multiplexer selector. The actual relocated HC11 OPTION register written by stock reset is `$3039`.

`source/replacement_os/hal/adc_read.asm` now uses the corrected PORTD/mux semantics.

## Current repo index

Primary state/authority:

- `docs/WORKING_STATE.md`
- `docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md`
- `docs/closeout/7427_COMPLETION_STATUS.md`
- `docs/implementation/ROM_FIRST_BUILD_PATH.md`

Replacement ROM/source:

- `source/replacement_os/7427_rom.asm`
- `source/replacement_os/include/target_layout.inc`
- `source/replacement_os/include/runtime_abi.inc`
- `source/replacement_os/core/*.asm`
- `source/replacement_os/hal/*.asm`
- `source/replacement_os/hal/*.inc`

Frozen planning data:

- `maps/planning/v1_configuration_variables.csv`
- `maps/planning/v1_module_interface_matrix.csv`
- `maps/planning/v1_calibration_manifest.csv`
- `maps/planning/v1_table_geometry.csv`
- `maps/planning/v1_degraded_operation_policy.csv`
- `maps/telemetry/v1_adx_manifest.csv`

Stock evidence/source:

- `source/31/BMHM_HAC_ORG_7100_to_end.asm`
- `docs/contracts/*.md`
- `maps/contracts/*.csv`
- `maps/full/hardware_access_map_v0.3.csv`
- `maps/current/hardware_access_map_hw_only.csv`

Historical/bench evidence remains under:

- `docs/bench/`
- `maps/bench/`
- `docs/tests/`
- `tests/static/`
- `source/minimal_os/`

Those artifacts remain useful evidence but no longer define the project frontier when they conflict with the current working-state/implementation authorities.

## Verification

ROM bootstrap structural checks:

```text
python tools/verify_rom_bootstrap.py
```

The verifier currently enforces:

- low-RAM allocation remains below the stock stack
- exactly 32 vector entries cover `$FFC0-$FFFE`
- external reset points to `RESET_ENTRY`
- the first ROM master contains no production-output commit calls
- ADC mux semantics identify `$3008` as PORTD
- reset-time OPTION uses the source-proven `$39` offset (`$3039` after relocation)

An HC11 assembler/toolchain and binary/map verification are the next build-layer addition.

## Next work order

```text
1. assemble/verify source/replacement_os/7427_rom.asm and inspect its binary/map
2. enforce actual ROM/RAM/vector collision checks from assembler output
3. bring up read-only ADC acquisition
4. bring up read-only REF acquisition and configurable cranking RPM visibility
5. add the base scheduler timer interrupt
6. add SCI/ALDL engine-off debug transport
7. add calibration header/integrity and real calibration objects as algorithms require them
8. complete the full spark/EST preserved island
9. implement engine-running modules in frozen interface order
10. generate/maintain XDF and ADX definitions from the actual built layouts
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid parallel `almost same` copies unless there is a real branch/release reason.
