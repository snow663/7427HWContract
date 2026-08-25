# BMHM 0.3.5 planning trace — cold fast-idle spark authority

## Evidence from 2026-08-25 15:25:47 cold-start log

At ~31.2 C coolant and closed corrected TPS, BMHM 0.3.4 shows:

- desired fast-idle target intermittently ~1250 RPM
- actual RPM ~1675-1725 RPM
- IAC present/desired already retracting from ~128 toward ~110 steps
- RPM closed-loop reported enabled
- Idle Flag OFF
- Idle Spark Enabled = false
- Spark Advance fixed at 38.3 deg
- Start-Up Spark Filter Flag = Complete

The key observation is that spark is not being used as a fast-idle governor. It remains fixed at 38.3 deg for the entire high-RPM cold period.

Near engine run time 189-190 s, coolant ~57.5 C and IAC essentially unchanged at ~62 steps, TRUE IDLE finally becomes active. At that transition:

- Idle Spark Enabled changes false -> true
- spark drops abruptly from 38.3 deg to ~26.4-27.1 deg
- desired idle is ~1087 RPM
- actual RPM is ~1100 RPM

This shows the excessive cold fast-idle speed is strongly tied to spark-state authority, not simply IAC command magnitude.

## Source trace

### Base spark table selection

At `$A70C-$A72A`:

- `$4166` = open-TPS spark table
- `$428A` = closed-throttle spark table
- selection is controlled by `L0050.b6`

Relevant flow:

```text
A70C  LDX #$4166
A70F  BRCLR L0050,#$40,A716
A713  LDX #$428A
...
A727  JSR LF4DE
A72A  STAA L01F8
```

`L0050.b6` is effectively the idle-spark-active state:

- `$A8B1` clears it when idle spark is bypassed.
- `$A903` sets it after the idle spark correction path executes.

Therefore, while BMHM fast idle is above the TRUE-IDLE RPM window, the 0.3.2/0.3.3/0.3.4 idle-spark gate keeps `L0050.b6` clear. The spark routine then continues using the OPEN-TPS base spark table even though corrected TPS is physically closed.

This is why the cold log can sit at 38.3 deg with TPS = 0%.

### Idle spark feedback path

At `$A84E-$A903`, stock `$31` contains a genuine RPM-error-based idle spark controller.

Qualification begins near `$A857` and uses:

- corrected TPS `$01D9`
- coolant threshold `$415D`
- desired idle RPM `$0857`
- filtered RPM `$0063`

Overspeed/underspeed error drives the idle-spark correction tables:

- `$44F0` — IAC overspeed spark retard correction vs RPM error / load
- `$4502` — underspeed idle spark advance vs RPM error / load
- `$451B` — derivative idle spark correction

When the path succeeds, `$A903` sets `L0050.b6`.

### Startup spark adder is not the cause

Main spark assembly at `$A7DB-$A81B` includes startup spark term `$02CB`:

```text
A7EF LDAB L02CB ; START UP SPK ADV
A7F2 ABX
```

However the uploaded cold log reports `Start-Up Spark Filter Flag = Complete` essentially immediately after run begins, while spark remains exactly 38.3 deg for ~3 minutes. The persistent 38.3-deg value is therefore not explained by the short startup spark filter term.

## Architectural consequence

BMHM 0.3.3 added a STARTUP FAST-IDLE state for IAC authority, but idle spark still requires centralized TRUE IDLE. That is inconsistent with the intended Motronic-style architecture.

STARTUP FAST IDLE should have its own spark authority using the same coolant-dependent desired RPM target as the fast-idle IAC controller.

Proposed behavior:

```text
corrected TPS closed
AND startup-fast-idle still eligible
AND cold-offset/startup state active
    -> FAST IDLE
    -> closed-throttle spark table
    -> RPM-error idle spark feedback enabled
    -> desired RPM = coolant fast-idle target

first real throttle opening
    -> latch FAST IDLE off
    -> normal DRIVE / DECEL / TRUE-IDLE state model resumes
```

The preferred implementation is to allow the existing stock idle-spark controller to run during FAST IDLE rather than invent a new fixed-retard table. That controller already has overspeed retard, underspeed advance, derivative correction, and load dependence.

The remaining design issue before BMHM 0.3.5 is the ordering of desired-RPM `$0857` writes. The fast-idle target must be authoritative before the spark RPM-error path reads `$0857`; the 0.3.4 log shows `$0857` alternating between the fast-idle target and the stock ~887-RPM value.

## Validation target for BMHM 0.3.5

On a ~30-40 C cold start with TPS closed:

- FAST-IDLE desired RPM should remain stable around its coolant target.
- Idle Spark Enabled should become active during FAST IDLE, even though TRUE-IDLE `$0050.b7` is still clear.
- Spark should no longer stay fixed at 38.3 deg while actual RPM is hundreds of RPM over target.
- Overspeed should produce immediate spark retard through the stock idle-spark controller.
- First throttle opening should cancel FAST IDLE, and later closed-throttle decel above the TRUE-IDLE RPM window must not re-enable idle spark.
