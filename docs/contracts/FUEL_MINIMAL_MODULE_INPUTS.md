# Fuel Minimal Module Inputs

## Purpose

Define the input boundary for a minimal speed-density TBI fuel module that ultimately commands EFI pulsewidth through `$3FCE`.

This document does not implement fuel math and does not tune calibration values.

## Output Contract

Owned by:

- `EFI_PW_3FCE_CONTRACT.md`
- `EFI_PW_UNITS.md`
- `MINIMAL_EFI_PW_WRITER.md`

Output:

```text
D = EFI pulsewidth counts in 1/65536 second units
STD $3FCE
```

## Required Input Classes

| Input class | Required? | Source type | Calibration dependency | Notes |
|---|---:|---|---|---|
| RPM | `required` | sensor / REF/DRP period / RPM state | source trace, no direct calibration section | Needed for speed-density fuel scheduling, crank/run, AE/DFCO/PE gates. |
| MAP / load | `required` | sensor / MAP ADC/scaled MAP | 91 $4CEA-$4CF2; 115 $4EB7-$4EC1; 136 $5067-$5071 | Primary speed-density load axis and VE/fuel correction dependency. |
| TPS / throttle state | `likely_required` | sensor / TPS ADC/scaled TPS | 77 $4BEA-$4C03; 81-84 $4C73-$4C96; 97-98 $4D5B-$4D7B | Needed for transient and mode gates; can be simpler for first open-loop fuel. |
| coolant temperature | `required` | sensor / CTS/scaled coolant | 21 $452D-$4536; 62-64 $4A36-$4A55; 73-76 $4B97-$4BE9; 102 $4DC2-$4DCC | Required for crank fuel, warmup, afterstart, and open-loop correction. |
| battery voltage | `required` | sensor / L00A7 battery volts VDC/10 candidate | 71 $4B75-$4B85; 114 $4EB6-$4EB6 | Battery voltage is needed for injector offset/deadtime and voltage protection. |
| baro / altitude basis | `likely_required` | sensor / BARO/MAP-derived baro | 25 $4558-$4584; 45 excluded EGR baro; 142 $50FA-$5109; 151 $5151-$5163 excluded trans | Needed for altitude/load correction; use only non-excluded sensor/fuel-relevant sections. |
| crank/run state | `required` | state / engine running / crank flags | 53 $494A-$494E; 153-155 $5603-$56AF | Separates crank fuel from run fuel and validates pulse enable state. |
| closed-loop permission state | `optional_initially` | mode_gate / closed-loop O2 enable/permission | 52 $4914-$4949; 55 $4975-$4979 | Optional initially; first runnable module can be open-loop with simple gate. |
| DFCO permission / zero fuel gate | `required` | safety_gate / DFCO/no-fuel flag and zero gate | 54 $494F-$4974 is trans_excluded in index but comments include decel; use source proof required | Must preserve no-fuel behavior; do not pull trans/decel baggage blindly from calibration index. |
| PE permission state | `optional_initially` | mode_gate / PE enable/thresholds | 79 $4C26-$4C52; 80 $4C53-$4C72; 196 $5F30-$5F40 | Needed for load enrichment eventually; can be coarse/optional for first safe loop if limits are conservative. |
| AE transient state | `optional_initially` | correction / AE/accel fuel state | 52 $4914-$4949; 58 $49BC-$49D0; 101 $4D92-$4DC1 | Refinement item; needed for drivability, but not first static output boundary. |
| base VE / airflow table input | `required` | calibration / VE/MAP/RPM table and airflow basis | 115 $4EB7-$4EC1; 116 $4EC2-$4EC9; 117 $4ECA-$4F01; 137 $5072-$5079; 138 $507A-$50AC; 145-147 $5130-$5150 | Core speed-density base airflow/fuel dependency. |
| injector flow constant | `required` | output_scale / IFR / injector flow scalar | not confidently isolated in index; source trace required | Required for BPW calculation; not safe to infer solely from stock index. |
| injector deadtime / battery correction | `required` | correction / battery offset/deadtime table candidate | 69 $4B5B-$4B63; 70 $4B64-$4B74; 71 $4B75-$4B85; 72 $4B86-$4B96 | Required to avoid low-voltage and low-PW error; exact units still need source/bench validation. |
| low-PW correction / transfer function | `required` | correction / new transfer table / low-PW model | not stock; future tests/static vectors | Project-specific required correction due known TBI low-PW nonlinearity/floor. |
| warmup enrichment | `required` | correction / warmup/coolant fuel modifiers | 9 $43AF-$4439; 60 $49E6-$49F5; 62-64 $4A36-$4A55; 68 $4B49-$4B5A | Required for cold/hot open-loop operation. |
| afterstart enrichment | `likely_required` | correction / afterstart/restart fuel state | 60 $49E6-$49F5; 61 $49F6-$4A35; 73-76 $4B97-$4BE9 | Likely required for stable start/run transition; keep separated from full GM strategy. |
| crank fuel | `required` | calibration / crank fuel tables/scalars | 62 $4A36-$4A45; 63 $4A46-$4A55; 64 $4A56-$4B16; 73 $4B97-$4BA6; 74 $4BA7-$4BB6 | Required before runnable start sequence. |
| target AFR / stoich basis | `required` | calibration / target AFR / commanded equivalence | 5 $4088-$408E; 52 $4914-$4949; 66 $4B20-$4B2F; 67 $4B30-$4B48; 86-87 $4C9D-$4CBE; 92 $4CF3-$4D03 | Required for final commanded fuel mass; keep stoich configurable. |
| fuel enable / no-fuel gate | `required` | safety_gate / fuel enable/no-fuel flag | source trace required; not calibration-only | Safety gate must be explicit even if simple. |
| EFI PW unit conversion | `required` | output_scale / PW counts = seconds * 65536 | EFI_PW_UNITS; no calibration section | Final output unit for D before STD $3FCE. |

## Minimal Fuel Pipeline

```text
sensor acquire
→ operating mode gates
→ base airflow / VE
→ commanded fuel mass / BPW
→ warmup / afterstart / crank modifiers
→ AE / PE / DFCO gates
→ injector model correction
→ low-PW transfer correction
→ EFI PW counts
→ $3FCE writer
```

## Initial Required Set

These are required or likely required for the first runnable open-loop speed-density TBI module:

```text
RPM
MAP
coolant temperature
battery voltage
baro / altitude basis
base VE / airflow calibration
injector flow constant
target AFR / stoich basis
warmup enrichment
crank fuel
afterstart enrichment
fuel enable / no-fuel gate
DFCO zero gate
injector deadtime / battery correction
low-PW transfer correction
EFI PW unit conversion
```

## Optional / Bench-Gated Initially

```text
closed-loop trim
PE refinement
AE refinement
wall-wetting / fuel film
decel fuel modifiers beyond DFCO
idle-specific fuel correction
```

## Explicitly Excluded

- transmission torque management unless spark/fuel hardware contract proves required
- EGR fuel/spark corrections
- EVAP purge fuel trims
- emissions-only diagnostics
- closed-loop trim complexity beyond a simple optional correction gate

## Excluded Fuel-Adjacent Baggage

| Input | Module candidate | Relevance | Reason |
|---|---|---|---|
| TCC / transmission tables | `trans_excluded` | `excluded` | transmission strategy excluded unless hardware-required |
| EGR correction tables | `egr_excluded` | `excluded` | EGR/emissions strategy excluded |
| EVAP / purge tables | `evap_excluded` | `excluded` | EVAP/purge strategy excluded |

## Unknown / Unresolved Fuel Inputs

| Input | Status | Notes |
|---|---|---|
| unknown fuel-adjacent sections | `unknown` | Keep visible for later tracing; do not guess or promote. |

## Bench / Source Gates

- `$3FCE` unit confirmation
- injector low-PW transfer validation
- DFCO zero-gate behavior
- battery/deadtime behavior
- crank/warmup enrichment source mapping
- fuel enable/no-fuel safety behavior
- injector flow/fuel pressure basis

## Discipline

Calibration sections are not marked `required` merely because they exist. The input becomes required only when a hardware/source contract or first minimal runnable fuel path needs it.

Transmission, EGR, EVAP, and emissions sections remain excluded unless a later hardware contract proves they are hardware-required.

## Machine-Readable Output

`maps/contracts/fuel_minimal_module_inputs.csv`

## Next Module Input Boundary

After fuel, do:

```text
SPARK_MINIMAL_MODULE_INPUTS
IAC_MINIMAL_MODULE_INPUTS
```
