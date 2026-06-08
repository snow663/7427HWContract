# Calibration Source Index

## Purpose

Index the `$31` HAC calibration source and classify calibration sections by minimal-OS module relevance.

This document does not replace the hardware contracts. Hardware contracts define what the minimal OS must drive. This index identifies which calibration data may feed those modules.

No tuning changes are made by this index.

## Source

`31_HAC_calibration_extract_nowrap.html`

## Source Summary

- section_count: 226
- record_count: 11916
- fcb_count: 11431
- fdb_count: 485
- min_data_address: $4000
- max_data_address: $70FF
- parse_error_count: 0
- warning_count: 96

## Classification Rules

Fuel-related sections map to fuel only if they appear to feed VE, airflow, BPW, crank fuel, warmup/afterstart, AE, PE, DFCO, injector correction, or battery/deadtime.

Spark-related sections map to spark only if they appear to feed spark advance, startup spark, knock/retard, spark latency, or RPM/MAP spark tables.

IAC/idle sections map to `iac_idle` only if they appear to feed desired idle, crank IAC, park position, IAC step/cadence, or idle correction.

Transmission, EGR, EVAP, and emissions sections stay excluded unless a hardware contract proves they are required.

Exclusion rules are applied before spark/fuel rules. This prevents sections such as EGR spark correction from being pulled into the minimal spark module by the word `spark` alone.

## Output

`maps/contracts/calibration_source_index.csv`

## Module Candidate Counts

| Module candidate | Sections |
|---|---:|
| `crank_start` | 18 |
| `egr_excluded` | 17 |
| `evap_excluded` | 4 |
| `fuel` | 24 |
| `iac_idle` | 36 |
| `sensor_scaling` | 33 |
| `spark` | 19 |
| `spark_latency` | 1 |
| `trans_excluded` | 49 |
| `unknown` | 24 |
| `warmup_afterstart` | 1 |

## Minimal-OS Relevance Counts

| Relevance | Sections |
|---|---:|
| `bench_gated` | 56 |
| `excluded` | 70 |
| `likely_required` | 76 |
| `unknown` | 24 |

## Excluded Strategy Baggage

The following sections are intentionally excluded unless a future hardware contract proves otherwise:

| Section | Range | Module | Title | Reason |
|---:|---|---|---|---|
| 1 | `$4000-$4035` | `evap_excluded` | EPROM ID | EVAP/purge strategy excluded |
| 2 | `$4036-$4046` | `evap_excluded` | %DC gm/sec AIRFLOW | EVAP/purge strategy excluded |
| 3 | `$4047-$4076` | `evap_excluded` | %D.C. gm/sec AIRFLOW | EVAP/purge strategy excluded |
| 6 | `$408F-$4165` | `egr_excluded` | L408D FCB 128 ; 0 14.7 | L408E FCB 128 ; 0 15.5 | RPM REACTION TEMP COMPONENT vs RPM & AIR FLOW | 06-30-1999 Dissassemby of BMHM | 17 COL x 9 BLOCKS = 153 BYTES | TBL = .3333333 * (Deg C + -300 Bias) | EGR/emissions strategy excluded |
| 36 | `$46F9-$4709` | `egr_excluded` | END OF SPARK PARAM'S | EGR PARAM'S | TYPE $31 PCM | EGR ENABLE QUALIFICATIONS | Dissassemby of BMHM, TYPE $31 ECM | 7.4L V8, TYPE $31 ECM | EGR/emissions strategy excluded |
| 37 | `$470A-$470A` | `egr_excluded` | 0 = VAC | EGR/emissions strategy excluded |
| 38 | `$470B-$475F` | `egr_excluded` | 09-18-2000 Dissassemby of BMHM | 9 COL x 9 BLOCKS = 81 BYTES | TBL = 2.56 * PCT EGR | ORG $470A ; 0 = VAC | L470A FCB 0 ; SEL LOAD MODE 1 = MAP | 2 = ALT MAP | EGR/emissions strategy excluded |
| 39 | `$4760-$4766` | `egr_excluded` | MULT DEG C COOL | EGR/emissions strategy excluded |
| 40 | `$4767-$4789` | `egr_excluded` | EGR GAIN FACTOR vs BARO & MAP | FOR BP EGR WITH 0 TO DISABLE EGR | OR WITH 128 TO ENABLE EGR | 09-18-2000 Dissassemby of BMHM | 4 COL x 8 BLOCKS = 32 BYTES | TBL = 1.28 * GAIN MULT | EGR/emissions strategy excluded |
| 41 | `$478A-$47CD` | `egr_excluded` | (BP EGR) | TBL = 00 = NO FUEL REDUCTION | = FF = 25% FUEL REDUCTION | 09-18-2000 Dissassemby of BMHM | 13 COL x 5 BLOCKS = 65 BYTES | TBL = 10.24 * FUEL% | EGR/emissions strategy excluded |
| 42 | `$47CE-$47D3` | `egr_excluded` | FILT COEF gms/sec | EGR/emissions strategy excluded |
| 43 | `$47D4-$47E4` | `egr_excluded` | Kpa PSI gms/sec flow | EGR/emissions strategy excluded |
| 44 | `$47E5-$4855` | `egr_excluded` | L47E4 FCB 132 ; 41.3 5.9 256 | %EGR FLOW vs EGR VALVE PRESS DROP and | LINEAR EGR POSIT, (or EVRV D.C.) | 09-18-2000 Dissassemby of BMHM | 10 COL x 11 BLOCKS = 110 BYTES | TBL = 2.56 * %Press Drop | EGR/emissions strategy excluded |
| 45 | `$4856-$485E` | `egr_excluded` | FACTOR Kpa baro | EGR/emissions strategy excluded |
| 46 | `$485F-$485F` | `egr_excluded` | EGR SPARK CORRECTION vs RPM & LOAD | (Load = %EGR OR Vac) | SEE BIAS AT L413A, (0 DEG) | Dissassemby of BMHM | 13 X 5 LINES | TABLE = SPK * 256/90 | EGR/emissions strategy excluded |
| 47 | `$4860-$48A9` | `egr_excluded` | SEE BIAS AT L413A, (0 DEG) | Dissassemby of BMHM | 13 X 5 LINES | TABLE = SPK * 256/90 | ORG $485F ; | L485F FCB 1 ; SEL VAC, (0 - %EGR) | EGR/emissions strategy excluded |
| 48 | `$48AA-$48AF` | `egr_excluded` | %D.C. % POS ERR | EGR/emissions strategy excluded |
| 49 | `$48B0-$48B5` | `egr_excluded` | FACTOR % POS ERR | EGR/emissions strategy excluded |
| 50 | `$48B6-$48F6` | `egr_excluded` | FACTOR % POS ERR | EGR/emissions strategy excluded |
| 54 | `$494F-$4974` | `trans_excluded` | L494B FCB 110 ; 477 mvdc LEAN o2 Thresh at IDLE | L494C FCB 119 ; 516 mvdc MEAN o2 Thresh at IDLE | L494D FCB 6 ; 150 msec PROP DURATION OFFSET AT IDLE | (Instead OF TBL L4D28) | L494E FCB 8 ; 100 msec PC CNT USE TRIGGER | transmission strategy excluded unless hardware-required |
| 113 | `$4E26-$4E91` | `egr_excluded` | MULT DRP'S | EGR/emissions strategy excluded |
| 121 | `$4F02-$4F31` | `trans_excluded` | Sec's Deg c | transmission strategy excluded unless hardware-required |
| 126 | `$4F6E-$4F91` | `evap_excluded` | RPM/12.5 Deg c COOL | EVAP/purge strategy excluded |
| 153 | `$510A-$5124` | `trans_excluded` | FACTOR %TPS ERROR | transmission strategy excluded unless hardware-required |
| 158 | `$5151-$5163` | `trans_excluded` | FACTOR BARO Kpa | transmission strategy excluded unless hardware-required |
| 159 | `$5164-$517D` | `trans_excluded` | % FULL LD MPH | transmission strategy excluded unless hardware-required |
| 161 | `$518F-$55F4` | `trans_excluded` | L518D FDB 00000 ; 31.25 Hz LOWER LIMIT | $31 REMOTE BROADCAST MODE | REMOTE MESSAGE SCHEDULE TABLE | (POLLING FORMAT) | (1 FOR EACH MINOR LOOP) | 0000 ADDRESS'S ARE IGNNORED BY PGM | transmission strategy excluded unless hardware-required |
| 165 | `$5961-$5BCF` | `trans_excluded` | L595E FCB 0 ; 0 14 | L595F FCB 0 ; 0 15 | L5960 FCB 0 ; 0 16 | 09-20-2000 Dissassemby of BMHM | 17 COL x 17 BLOCKS = 289 BYTES | TBL = 1 * PSI | transmission strategy excluded unless hardware-required |
| 166 | `$5D00-$5D3D` | `trans_excluded` | ALL ZERO'D L5BD0 TH L5CFF | BMHM/9483 P/N 16209482 | PCM $31 TRANSMISSION CALIBRATION | MY 95 L19, C2, C3, K2, K3, R2, NM8, | SS BY BPRJ/0287 P/N 16220287 | ECM P/N 16197427 or 16156930 | transmission strategy excluded unless hardware-required |
| 167 | `$5D3E-$5D43` | `trans_excluded` | MPH GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 168 | `$5D44-$5D49` | `trans_excluded` | MPH GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 169 | `$5D4A-$5D4F` | `trans_excluded` | MPH GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 170 | `$5D50-$5D55` | `trans_excluded` | MPH GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 171 | `$5D56-$5D5A` | `trans_excluded` | RPM GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 172 | `$5D5C-$5D60` | `trans_excluded` | RPM GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 173 | `$5D62-$5D66` | `trans_excluded` | RPM GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 174 | `$5D68-$5D6C` | `trans_excluded` | RPM GEAR SHIFT | transmission strategy excluded unless hardware-required |
| 175 | `$5D6E-$5D7E` | `trans_excluded` | MPH %TPS | transmission strategy excluded unless hardware-required |
| 176 | `$5D7F-$5D8F` | `trans_excluded` | MPH %TPS | transmission strategy excluded unless hardware-required |
| 177 | `$5D90-$5DA0` | `trans_excluded` | MPH %TPS | transmission strategy excluded unless hardware-required |
| ... | ... | ... | 30 additional excluded sections in CSV | ... |

## Unknown / Unclassified Sections

Unknown sections are listed rather than silently guessed:

| Section | Range | Title | Notes |
|---:|---|---|---|
| 33 | `$461C-$465C` | Msec RPM | no confident module keyword; keep listed rather than guessing |
| 65 | `$4B17-$4B1F` | Factor Deg c coolant | no confident module keyword; keep listed rather than guessing |
| 75 | `$4B93-$4BA4` | FACTOR DEG C COOL | no confident module keyword; keep listed rather than guessing |
| 80 | `$4C44-$4C54` | SEC'S Deg c cool | no confident module keyword; keep listed rather than guessing |
| 81 | `$4C55-$4C5A` | MULT AIR FLOW | no confident module keyword; keep listed rather than guessing |
| 109 | `$4DCD-$4DDD` | DRP'S DEG C COOL | no confident module keyword; keep listed rather than guessing |
| 132 | `$4FD7-$4FE1` | . %FLOW RPM ERROR | no confident module keyword; keep listed rather than guessing |
| 138 | `$5019-$5023` | %FLOW RPM ERROR | no confident module keyword; keep listed rather than guessing |
| 150 | `$50EF-$50F9` | Gain RPM/Sec | no confident module keyword; keep listed rather than guessing |
| 160 | `$517E-$518D` | %FULL LD MPH | no confident module keyword; keep listed rather than guessing |
| 162 | `$55F5-$5718` | L55F3 FCB $D9 ; | L55F4 FCB $0039 ; | 3d TBL .... Vs. ... Vs. RPM | 09-20-2000 Dissassemby of BMHM | 17 COL x 17 BLOCKS = 289 BYTES | TBL = 1 * PSI | no confident module keyword; keep listed rather than guessing |
| 163 | `$5719-$583C` | L5716 FCB 0 ; 0 14 | L5717 FCB 0 ; 0 15 | L5718 FCB 0 ; 0 16 | 09-20-2000 Dissassemby of BMHM | 17 COL x 17 BLOCKS = 289 BYTES | TBL = 1 * PSI | no confident module keyword; keep listed rather than guessing |
| 164 | `$583D-$5960` | L583A FCB 0 ; 0 14 | L583B FCB 0 ; 0 15 | L583C FCB 0 ; 0 16 | 09-20-2000 Dissassemby of BMHM | 17 COL x 17 BLOCKS = 289 BYTES | TBL = 1 * PSI | no confident module keyword; keep listed rather than guessing |
| 200 | `$60CE-$6125` | L60CC FCB 1 ; 1 15 | L60CD FCB 1 ; 1 16 | FILE VEH SPD | 09-20-2000 Dissassemby of BMHM | 11 COL x 17 BLOCKS = 187 BYTES | TBL = 128 * PSI | no confident module keyword; keep listed rather than guessing |
| 201 | `$6126-$6154` | L6123 FCB 128 ; 1.000 2 | L6124 FCB 128 ; 1.000 3 | L6125 FCB 128 ; 1.000 4 | 09-20-2000 Dissassemby of BMHM | 11 COL x 4 BLOCKS = 44 BYTES | TBL = 128 * PSI | no confident module keyword; keep listed rather than guessing |
| 202 | `$6155-$6183` | L6152 FCB 128 ; 1.000 8 | L6153 FCB 128 ; 1.000 9 | L6154 FCB 138 ; 1.078 10 | 09-20-2000 Dissassemby of BMHM | 11 COL x 11 BLOCKS = 121 BYTES | TBL = 128 * PSI | no confident module keyword; keep listed rather than guessing |
| 203 | `$6184-$61B2` | L6181 FCB 128 ; 1.000 8 | L6182 FCB 128 ; 1.000 9 | L6183 FCB 138 ; 1.078 10 | 09-20-2000 Dissassemby of BMHM | 11 COL x 11 BLOCKS = 121 BYTES | TBL = 128 * PSI | no confident module keyword; keep listed rather than guessing |
| 206 | `$62D7-$63FA` | L63F8 FCB 58 ; 58 120 | L63F9 FCB 58 ; 58 124 | L63FA FCB 58 ; 58 128 | 09-20-2000 Dissassemby of BMHM | 17 COL x 17 BLOCKS = 289 BYTES | TBL = 1 * PSI | no confident module keyword; keep listed rather than guessing |
| 208 | `$651F-$6642` | L651D FCB 255 ; 255 60 | L651E FCB 255 ; 255 64 | MANUAL MODE LINE PRESS 64 - 128 MPH | 09-20-2000 Dissassemby of BMHM | 17 COL x 17 BLOCKS = 289 BYTES | TBL = 1 * PSI | no confident module keyword; keep listed rather than guessing |
| 212 | `$6676-$66DB` | L6673 FCB 143 ; 15 87.5 | L6674 FCB 143 ; 15 93.8 | L6675 FCB 143 ; 15 100.0 | 09-20-2000 Dissassemby of BMHM | 128 BYTES | TBL = 1 * | no confident module keyword; keep listed rather than guessing |
| 215 | `$66F0-$66F2` | L66EB FCB 118 ; -10 48 | L66EC FCB 118 ; -10 52 | L66ED FCB 118 ; -10 56 | L66EE FCB 118 ; -10 60 | L66EF FCB 118 ; -10 64 | PRESS MOD TBL BREAK POINTS FOR L66F3 | no confident module keyword; keep listed rather than guessing |
| 217 | `$6704-$6706` | L66FF FCB 128 ; 0 48 | L6700 FCB 128 ; 0 52 | L6701 FCB 128 ; 0 56 | L6702 FCB 128 ; 0 60 | L6703 FCB 128 ; 0 64 | PRESS MOD TBL BREAK POINTS FOR L6707 | no confident module keyword; keep listed rather than guessing |
| 225 | `$6BF9-$6E58` | L6BF4 FCB 116 ; 58 75.0 | L6BF5 FCB 116 ; 58 81.3 | L6BF6 FCB 116 ; 58 87.5 | L6BF7 FCB 116 ; 58 93.8 | L6BF8 FCB 116 ; 58 100.0 | 09-20-2000 Dissassemby of BMHM | no confident module keyword; keep listed rather than guessing |
| 226 | `$6E59-$70FF` | L6E56 FCB 100 ; | L6E57 FCB 70 ; | L6E58 FCB 110 ; | 09-20-2000 Dissassemby of BMHM | 17 COL x 17 BLOCKS = 289 BYTES | TBL = 1 * PSI | no confident module keyword; keep listed rather than guessing |

## Required Discipline

Do not mark a calibration section as `required` merely because it exists in the stock calibration. A section becomes required only when a hardware/source module contract proves that the minimal OS needs it.

Current index relevance is conservative:

```text
likely_required = probably needed by future math/module planning, but not final
bench_gated     = module-relevant but physical hardware behavior or units still need proof
calibration_only= useful ID/diagnostic/reference data, not a runtime control requirement yet
excluded        = out-of-scope strategy baggage unless future hardware contract proves otherwise
unknown         = not confidently classified; keep visible for later source tracing
```

## Next Use

Use this index when defining fuel, spark, IAC, crank/start, warmup, battery/deadtime, and debug module inputs. Do not use it to bypass hardware-contract requirements.
