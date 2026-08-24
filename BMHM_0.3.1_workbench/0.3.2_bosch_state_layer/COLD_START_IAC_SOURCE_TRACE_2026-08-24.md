# Cold-start IAC / fast-idle source trace — 2026-08-24

Basis: `$31_HAC.SRC` / BMHM source trace plus `BMHM_0.3.2.bin` and log `2026-08-24_15.54.14.csv`.

This note records the source walk used to diagnose the excessive cold-start speed seen with BMHM 0.3.2. It is intentionally separate from the canonical contracts because the controller is still being reshaped experimentally.

## Log signature

The log begins at **27 s engine running time**, coolant about **35.8 C**, TPS **0.0%**, actual RPM **1675-1700**, desired idle about **887 RPM**, and IAC present/desired both **112 steps**. TRUE-IDLE, idle spark, and closed-loop IAC are off until RPM falls through the 0.3.2 true-idle window near 1100 RPM.

The important correction is that the log does **not** begin immediately after crank. By 27 s, both short after-start terms described below should already have expired. The long high-idle event is therefore dominated by the persistent coolant-based IAC cold offset, not the short after-start airflow adder.

## Initialization path — `$940A-$9537`

### Closed-loop IAC startup timers

`$9411-$9426` loads two coolant-indexed startup timers:

- `$4EF5-$4F01` -> `L0866`: IAC closed-loop enable delay after startup, RPM-high branch.
- `$4F02-$4F0E` -> `L0867`: IAC closed-loop enable delay after startup, RPM-low branch.

They are decremented at `$A288-$A297` and consulted at `$9A1B-$9A3C`.

The stock source therefore already distinguishes high-RPM and low-RPM startup entry into closed-loop idle control. BMHM 0.3.2 currently supersedes the VSS qualification at `$99F2` with the centralized TRUE-IDLE state, which means the stock high-RPM startup IAC-control path cannot gain authority while RPM remains above the TRUE-IDLE ceiling.

### Short after-start airflow adder

`$9429-$9432`:

- `$4EB8 = 60`: about 23% flow added after startup -> `L086B`.
- `$4EB9 = 1`: source comment identifies a 100 ms decay period -> `L086C`.

Runtime decay is `$A2DA-$A2F7`. `L086B` is decremented by one count when its period expires. With 60 initial counts and the source's 100 ms period description, this term is a short after-start catch, on the order of seconds rather than minutes.

`L086B` is added directly into final requested IAC flow at `$9787`.

At 27 s run time in the test log this term should already be zero, so it cannot explain the sustained 1675-RPM condition.

### Startup desired-RPM adder

`$9455-$945B` loads the coolant table `$4F6E-$4F7C` into `L085C`.

`$9473-$947C` initializes its decay timing:

- `$4EBA = 10`: 10 s before decay begins -> `L085E`.
- `$4EBB = 5`: source comment identifies 500 ms decay period -> `L085D`.

Runtime decay is `$A2FA-$A327`. One raw RPM-target count is removed per decay event. `L085C` is then added to the normal desired-idle target at `$993E-$994F`.

In the current calibration the relevant `$4F6E` cells are only a few raw counts (roughly tens of RPM). Even if present at startup, this term is gone well before the log begins at 27 s.

### Persistent coolant-based cold-offset airflow

`$94B5-$94D2` initializes two 16-bit cold-offset pairs:

- `$4ECF-$4EDB` -> `L02AD/L02AF`: DRIVE cold-offset airflow.
- `$4EC2-$4ECE` -> `L02A3/L02A5`: PARK/NEUTRAL cold-offset airflow.

`$94D5-$94DE` loads the coolant-indexed cold-offset delay `$4EDC-$4EE8` into `L0875`.

These are the long-lived startup-air terms that remain active after the short `L086B` and `L085C` terms have expired.

## Runtime cold-offset housekeeping — `$9FE9-$A0D8`

`$9FDE-$9FE6` first checks whether the cold offsets are nonzero. If either max-offset accumulator remains nonzero, `$9FE9` services the cold-offset timer.

When `L0875` reaches zero:

- `$9FF1-$9FFF`: max PARK offset `L02A5` is multiplied by `$4EBD`.
- `$A004-$A016`: PARK working offset `L02A3` is multiplied by `$4EBE` and constrained to the max accumulator.
- `$A019-$A027`: max DRIVE offset `L02AF` is multiplied by `$4EBD`.
- `$A02C-$A03E`: DRIVE working offset `L02AD` is multiplied by `$4EBF` and constrained to the max accumulator.

Current constants are stock here:

- `$4EBD = 250/256` ~= 97.66% max-offset decay multiplier.
- `$4EBE = 245/256` ~= 95.70% PARK working-offset multiplier.
- `$4EBF = 245/256` ~= 95.70% DRIVE working-offset multiplier.

`$A049-$A069` reloads `L0875` from the coolant delay table `$4EDC`, multiplied by airflow-dependent `$4EE9-$4EED`. In the current calibration the airflow multipliers are all 1.0, so the coolant table controls the delay directly.

`$A06C-$A0D3` selects/coordinates PARK versus DRIVE offset state using `L0036.b1` (`DRIVE`). The validation log reports Gear Select = Drive, so the DRIVE cold-offset path is the expected active branch for that run.

## Current cold-offset tables

### PARK / NEUTRAL `$4EC2-$4ECE`

This table is unchanged from stock BMHM.

| Coolant C | Raw | Approx % IAC flow |
|---:|---:|---:|
| -28 | 255 | 99.6 |
| -16 | 250 | 97.7 |
| -4 | 230 | 89.8 |
| 8 | 179 | 69.9 |
| 20 | 128 | 50.0 |
| 32 | 102 | 39.8 |
| 44 | 90 | 35.2 |
| 56 | 64 | 25.0 |
| 68 | 37 | 14.5 |
| 80 | 31 | 12.1 |
| 92 | 28 | 10.9 |
| 104 | 28 | 10.9 |
| 116 | 28 | 10.9 |

### DRIVE `$4ECF-$4EDB`

The running 0.3.2 calibration differs from stock BMHM in the 44-104 C region. Values below are the actual 0.3.2 bytes, with `%flow = raw / 2.56`.

| Coolant C | 0.3.2 raw | 0.3.2 %flow | Stock raw |
|---:|---:|---:|---:|
| -28 | 255 | 99.6 | 255 |
| -16 | 250 | 97.7 | 250 |
| -4 | 248 | 96.9 | 248 |
| 8 | 240 | 93.8 | 240 |
| 20 | 224 | 87.5 | 224 |
| 32 | 192 | 75.0 | 192 |
| 44 | 171 | 66.8 | 148 |
| 56 | 154 | 60.2 | 125 |
| 68 | 119 | 46.5 | 90 |
| 80 | 111 | 43.4 | 82 |
| 92 | 103 | 40.2 | 74 |
| 104 | 84 | 32.8 | 55 |
| 116 | 70 | 27.3 | 70 |

The initial ~36 C point is close to stock because both calibrations are identical at 32 C and diverge only by 44 C. The edited table does, however, preserve substantially more cold-offset airflow as the engine warms through roughly 44-104 C, extending the high-idle decay tail.

## Final requested IAC flow path — `$9752-$9899`

The controller builds requested airflow before converting it to IAC steps:

1. `$9752`: start with `L0862`.
2. `$9755`: add `L0871`.
3. `$975D-$9786`: apply integral/derivative idle-control corrections according to RPM error/direction.
4. `$9787`: add short after-start airflow `L086B`.
5. `$978C`: add power-steering airflow `L087B`.
6. further A/C / auxiliary corrections follow.
7. `$983D-$9855`: apply altitude compensation.
8. `$9883-$9899`: use `$4E92` IAC step-position-vs-flow linearization to convert requested airflow to motor steps, stored in `L0008`.

The cold-offset state is initialized into the open-loop IAC base state at startup and is maintained/decayed separately from the short after-start terms.

## Why the 0.3.2 log stays fast for so long

At 27 s run time:

- `L086B` short after-start flow should already be gone.
- `L085C` startup desired-RPM adder should already be gone.
- the desired-idle value reported by ALDL is only about 887 RPM.
- the IAC is nevertheless commanded to 112 steps and the engine runs ~1675-1700 RPM.

That combination points directly at the remaining open-loop cold-offset airflow as the active authority.

As coolant rises and the cold offset decays, desired IAC falls slowly from ~112 toward the 60s. Only when RPM crosses the BMHM 0.3.2 TRUE-IDLE entry window does the normal feedback idle controller receive authority, at which point IAC closes quickly and RPM converges to desired idle.

## Important interaction introduced by BMHM 0.3.2

Stock `$31` contains explicit high-RPM and low-RPM startup delays (`L0866/L0867`) before enabling closed-loop IAC. That is evidence that GM intended closed-loop IAC to be able to take control during startup even when RPM is still high, after a calibrated delay.

BMHM 0.3.2 currently makes `$99F2` obey centralized TRUE-IDLE, whose RPM window is 1100-enter / 1200-exit. As a result, closed-loop IAC cannot use the stock high-RPM startup path while the cold offset is holding the engine at 1200-1700 RPM.

This is the key source-level finding for the next revision.

## Next control direction

Do **not** simply lower the desired-idle table and do **not** blindly reduce all cold-offset airflow.

The cleaner Bosch/Motronic-like design is:

- corrected TPS supplies the virtual idle switch;
- TRUE-IDLE remains the warm idle / BLM-cell / idle-spark state;
- a separate FAST-IDLE IAC-control eligibility can exist while the virtual idle switch is closed and cold-offset/startup state is active;
- closed-loop IAC then controls an explicit coolant-dependent fast-idle RPM target instead of letting open-loop IAC steps determine engine speed;
- once fast-idle conditions expire, authority falls back to the normal TRUE-IDLE state.

A practical implementation can reuse the existing desired-idle-vs-coolant tables and/or the existing startup desired-RPM adder rather than adding another arbitrary airflow table. The DRIVE desired-idle table `$4F50-$4F5E` is already the active family in the logged state and is currently edited relative to stock.

The next binary should be chosen only after reviewing the 0.3.2 drive log so the new fast-idle qualification does not regress the DECEL/TRUE-IDLE behavior just validated by the state-layer work.
