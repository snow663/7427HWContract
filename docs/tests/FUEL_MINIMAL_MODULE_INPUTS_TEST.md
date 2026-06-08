# Fuel Minimal Module Inputs Test

## Goal

Verify that the fuel input-boundary planning artifact defines only the inputs needed to feed the existing `$3FCE` fuel output contract and does not create implementation code or import stock strategy baggage.

This test validates planning boundaries only. It does not tune, implement fuel math, or alter ASM.

## Required Files

```text
docs/contracts/FUEL_MINIMAL_MODULE_INPUTS.md
maps/contracts/fuel_minimal_module_inputs.csv
tools/build_fuel_minimal_module_inputs.py
docs/tests/FUEL_MINIMAL_MODULE_INPUTS_TEST.md
```

## Static Validation Tests

| Test | Expected |
|---|---|
| output dependency | `$3FCE` output dependency is present |
| unit dependency | `EFI PW counts in 1/65536 second units` is present |
| no-fuel gate | DFCO/no-fuel gate is represented |
| injector model | injector flow, deadtime/battery correction, and low-PW transfer correction are represented |
| calibration discipline | no calibration section alone marks an input required |
| exclusions | no trans/EGR/EVAP section is marked required |
| unknowns | unknown inputs/sections are listed, not guessed |
| source safety | no ASM/source writer file is created |

## Command

```bash
python tools/build_fuel_minimal_module_inputs.py \
  --cal-index maps/contracts/calibration_source_index.csv \
  --out-md docs/contracts/FUEL_MINIMAL_MODULE_INPUTS.md \
  --out-csv maps/contracts/fuel_minimal_module_inputs.csv
```

## Required Checks

```text
1. no trans/EGR/EVAP section is marked required
2. no calibration section alone marks an input required without source/hardware dependency
3. $3FCE output dependency is present
4. EFI PW unit conversion dependency is present
5. DFCO/no-fuel gate is represented
6. injector deadtime and low-PW correction are represented
7. unknowns are listed, not guessed
8. no ASM/source writer file is created
```

## Exclusion Discipline

These must remain excluded unless a later hardware contract proves otherwise:

```text
TCC/trans tables
EGR correction tables
EVAP/purge tables
emissions diagnostics
```

## Pass Criteria

```text
PASS:
  FUEL_MINIMAL_MODULE_INPUTS.md exists
  fuel_minimal_module_inputs.csv exists
  CSV uses controlled required_for_first_minimal_os values
  required inputs cite a hardware/source dependency
  excluded calibration baggage remains excluded
  unknown fuel-adjacent inputs remain visible
  no new ASM files are created
```

## Fail / Rework Criteria

```text
REWORK:
  any trans_excluded/egr_excluded/evap_excluded row is marked required
  any calibration-only row becomes required without a source/hardware contract
  DFCO/no-fuel gate is missing
  injector deadtime or low-PW correction is missing
  EFI PW unit conversion is missing
  a new fuel ASM writer is created by this pass
```

## Notes

This pass defines what must feed the future fuel calculation that produces:

```text
D = EFI pulsewidth counts in 1/65536 second units
STD $3FCE
```

It does not define the equations yet.
