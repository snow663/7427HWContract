# Milestone B Build Proof

## Toolchain

```text
MGTEK ASM11
68HC11 Cross Assembler V1.26 Build 144 for WIN32 (x86)
```

Source:

```text
source/replacement_os/7427_inputs_miniide.asm
```

Observed build result from the user's PC:

```text
0 warnings
0 errors
```

## Proven RAM layout

```text
$0000 RAW_TPS
$0001 RAW_MAP
$0002 RAW_O2
$0003 RAW_COOLANT
$0004 RAW_BATTERY
$0005 RAW_MAT_INV
$0006 RAW_REF_PERIOD_HI
$0007 RAW_REF_PERIOD_LO
$0008 ADC_TIMEOUT
$0009 SAMPLE_SEQUENCE
$000A RAM_ALLOC_END
```

The Milestone-B allocation occupies only `$0000-$0009`, well below `STACK_TOP=$03FF`.

## Proven ROM layout

```text
RESET_ENTRY                    $7100
INPUT_SAMPLE_LOOP              $711A
HAL_INIT_PROCESSOR_INPUT_SAFE  $712E
HAL_SERVICE_COP                $714F
HAL_ADC_SET_MUX_SELECT         $715A
HAL_ADC_START_WAIT             $716C
HAL_SAMPLE_PRIMARY_ADC         $7183
HAL_SAMPLE_COOLANT_BATTERY     $719C
HAL_SAMPLE_MAT                 $71B5
HAL_CAPTURE_REF_PERIOD         $71CA
HAL_FATAL_SAFE_LOOP            $71D2
ROM_CODE_END                   $71D8
vector table                   $FFC0-$FFFF
external reset vector          $FFFE -> $7100
```

The executable bytes occupy `$7100-$71D7`. There is no overlap with the vector table.

## Input hardware facts now exercised by the build

```text
HC11 relocated register base  $3000
PORTD                          $3008
DDRD                           $3009
ADCTL                          $3030
ADR1                           $3031
ADR2                           $3032
ADR3                           $3033
ADR4                           $3034
ASIC REF/DRP period            $3FC0
```

Stock startup evidence establishes `DDRD=$38`, making PORTD bits 3-5 outputs for the external analog-mux selector. Milestone B initializes only that input-path requirement and does not import the broader stock output/ASIC initialization.

## S-record / BIN proof

The uploaded ASM11 S-record was checksum-validated record by record and converted to a 65,536-byte image with unrepresented bytes filled `$FF`.

```text
BIN size:    65536 bytes
reset @FFFE: $7100
SHA-256:     28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

Reproducible converter:

```text
tools/s19_to_64k_bin.py
```

## Safety / interpretation boundary

Milestone B contains no injector, spark/EST, IAC, pump, or auxiliary-output command writes. It continuously samples the proven ADC paths and reads `$3FC0` into RAM.

The `$3FC0` REF/DRP read must not yet be interpreted as proven live REF observability on hardware. Stock firmware initializes the `$3FC0-$3FFA` ASIC/register island during startup; Milestone B deliberately does not perform those writes. Establishing the minimum read-only-safe ASIC initialization required for meaningful REF data is a later step.
