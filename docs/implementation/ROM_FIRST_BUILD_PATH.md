# 7427 ROM-First Implementation Path

## Decision

The replacement OS is built from the executable ROM outward.

The project will **not** freeze a complete binary-encoding matrix, RAM partition, XDF address map, or ADX packet map before implementation. The built ROM and its assembly/listing output are the placement authority.

## Fixed boundaries

The hardware contract already provides the fixed boundaries that matter:

```text
stock/replacement stack top       $03FF
HC11 reset register base          $1000
HC11 relocated register base      $3000
stock calibration/header region   $4000+
first replacement code ORG        $7100
HC11 vector window                $FFC0-$FFFF
external reset vector             $FFFE
additional stock-used RAM         $0800-$08FF
```

Hardware/ASIC addresses remain owned by the HAL/contracts.

## Allocation policy

### RAM

```text
module needs state
-> add semantic or HAL-private state declaration
-> assembler assigns actual location
-> listing/map proves no collision with stack/hardware
```

Do not reserve broad subsystem blocks merely for organizational symmetry.

### Calibration ROM

```text
implement feature
-> define required scalar/table
-> choose representation needed by implementation
-> allocate in ROM
-> assemble/inspect
-> expose actual address/scaling in XDF metadata
```

Frozen semantic units/table geometry remain design authority; addresses do not need to exist before the consuming code exists.

### XDF / ADX

The XDF describes the actual calibration layout of the built ROM. The ADX describes the actual telemetry packet/page implemented by the ROM. Semantic planning manifests define required concepts/channels, not preassigned offsets.

## Source roles

Maintainable modular authority:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/*.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
```

Self-contained ASM11 bring-up stages:

```text
7427_bootstrap_miniide.asm   Milestone A
7427_inputs_miniide.asm      Milestone B
7427_aldl_tx_miniide.asm     Milestone C
```

These proof-stage sources deliberately avoid include-path/toolchain friction. They are not intended to become a permanently divergent implementation; verified behavior is folded back into the modular source.

## Current checkpoint — 2026-08-19

### Milestone A: PROVEN

Bootstrap/reset/vector image assembled with ASM11 V1.26 Build 144 at 0 warnings / 0 errors. The deterministic 64 KiB image has reset `$FFFE -> $7100` and SHA256:

```text
c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

### Milestone B: PROVEN BUILD

Read-only ADC/REF acquisition image assembled with 0 warnings / 0 errors.

```text
RAM $0000-$0009
code $7100-$71D7
vectors $FFC0-$FFFF
reset $FFFE -> $7100
SHA256 28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

The `$3FC0` read is build-proven but not yet live-REF-proven because the stock ASIC/register initialization is intentionally absent.

### Milestone C: SOURCE READY / PROOF PENDING

`source/replacement_os/7427_aldl_tx_miniide.asm` adds engine-off SCI/ALDL observability on top of the Milestone-B acquisition approach.

It establishes the source-proven BMHM/TBI board-control baseline:

```text
$3FFC/$3FFD = $B93A
```

before ALDL read/modify/write, uses low-byte `$3FFD bit2` for the external ALDL driver, configures 8192-baud SCI, and transmits a 14-byte raw-input frame. Production actuator authority remains absent.

The next gate is assembly/listing/S19/BIN proof followed by engine-off bench proof.

## Increment rule

Advance one observable capability at a time:

```text
proven bootstrap
-> proven read-only ADC image
-> engine-off ALDL telemetry
-> live ADC proof
-> minimum safe ASIC initialization / live REF proof
-> integrate proven observability into modular master
-> engineering sensor pipeline
-> configurable REF geometry/lifecycle
-> calibration objects as algorithms require them
-> complete preserved spark/EST island
-> engine-running control modules
```

No production output becomes executable merely because its module is linked.

## Definition generation rule

For every implemented calibration or telemetry object retain:

```text
symbol
actual address
storage width
signedness
scaling / conversion
engineering unit
table dimensions / axes if applicable
```

That metadata follows executable allocation rather than preceding it.

## Evidence corrections retained

### ADC register identity

Stock `F275` proves:

```text
$3008 = relocated CPU PORTD, used for external ADC/mux selection
$3039 = relocated HC11 OPTION
```

The earlier `$3008 = OPTION` interpretation is superseded.

### ALDL board-control baseline

Stock BMHM/TBI startup writes `$B93A` to `$3FFC/$3FFD` before normal serial activity. Replacement ALDL bring-up must establish that known baseline before manipulating low-byte `$3FFD bit2`; preserving an unspecified reset value would leave neighboring board-control bits unknown.
