# Rev B single manual-idle candidate

Rev B combines the single manual-idle controller, target-relative deceleration
spark release and the cold-idle timing-table revision. It is a development
candidate built from the exact supplied Rev A, with its original retained as
the rollback image. No vehicle flash was performed.

| Item | Identity |
|---|---|
| Input | `0.3.12_engine_only_spark_idle_revA.bin` |
| Input SHA-256 | `d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e` |
| Output | `0.3.12_engine_only_manual_idle_revB.bin` |
| Output SHA-256 | `e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1` |
| Output checksum | `4E78`, big-endian at 4006 |
| Size / address model | 65,536 bytes; CPU ROM address equals file offset |
| Matching definition | `7427_0.3.12_Manual_Idle_RevB.xdf` |

## Idle strategy

Both Park/Drive strategies are replaced by
[the reviewed controller](../../source/manual_idle/README.md). There is one
FF60 coolant-index RPM schedule for starting/running, one runtime baseline,
bounded P/I action, startup-air fade, a TPS follower, stall recovery and a
simple A/C air adder. The learned baseline resets on restart/homing. Original
bank transfers, separate A/C learning banks, derivative and BLM-driven target
correction are absent. Main scheduling admission and the existing actuator
guard, phase driver, homing, service and air-to-position conversion remain.

The 39-byte calibration at 9F00..9F26 uses the source defaults. These are
initial development settings, including the cold-air curve, rather than a
fit of physical airflow against the truck logs. Internal air is not motor
steps or measured percent flow. Historical prototype identities and proof
reports remain recorded separately from the actual Rev B image.

## Deceleration spark

The complete old A97A..A9DF recovery body is replaced by an entry jump at A97A
to [decel_spark_gate.asm](../../source/manual_idle/decel_spark_gate.asm), at
9F40. Retard now applies only when both conditions hold:

- Fuel cut is currently active at RAM 0046.3.
- Actual RPM at 0063 exceeds the requested idle RPM at 0857 plus the shared
  IAC release margin at 9F17 (default 200 RPM).

Equality releases the correction. Byte addition overflow also releases it,
because no byte RPM can exceed that mathematical threshold. While admitted,
the base/coolant retard arithmetic, byte wrap and composite subtraction match
the resident active-DFCO instructions exactly. RAM 0051.5 is still set there:
AAF7 also uses it to select the DFCO minimum spark limit. This shared consumer
is preserved.

When either gate fails, the replacement clears 0051.5 and the saved retard
byte 0208, leaves the composite 01FD unchanged and continues at A9E0. It never
clears shared word 01F2 on this cleanup path. Startup still owns that word;
the admitted active-DFCO path retains the original reset. The removed
post-fuel recovery no longer reads 414F/4150/4151, and those controls are
omitted from the Rev B definition. 4152 remains the active-DFCO base retard;
zero can still leave a coolant term. There is no invented enable flag.

Changing 9F17 now changes both IAC release and the decel spark approach
threshold. The definition explicitly labels this sharing. The fuel idle
classifier's RPM margins remain fixed at +100/+200 RPM.

## Cold-idle base timing

The Rev A logs show mid-warm idle moving through a rising portion of the
single base table. Rev B changes 27 cells at nominal 1200, 1600 and 2000 RPM,
20..60 kPa. The base shelf is 27.421875 degrees through 1600 RPM at 20..50
kPa, with a 33.75-degree 2000-RPM shoulder. The 55/60-kPa columns blend into
each unchanged 65-kPa cell. The 400/600-RPM underspeed slope and existing
800/1000-RPM shelf remain. These are base-table degrees; retained startup,
coolant, knock and final limits still affect commanded timing.

Every 65..100-kPa cell is unchanged, including the prior loaded reduction.
Fueling calibration, knock code/calibration, spark command limits, vectors,
physical output writers and the engine-only helpers are unchanged by this
release. This does not claim identical runtime fueling: idle state and air
commands deliberately change.

## Definitions and maintained registers

Rev A and its original definition remain a separate rollback pair. The Rev A
and historical prototype XDF builders use the pinned Rev A ROM-role snapshot,
so advancing the maintained register cannot silently remove rollback controls.
Rev B uses the updated register and its own program fingerprint. Never choose
an XDF merely by mask number; 9F00..9F26 is executable code in Rev A.

The Rev B definition exposes the complete new calibration, omits the retired
Park/Drive controls and recovery gains, and retains shared fuel, driver and
conversion controls. The 50C7/50C8/50C9/50CE labels distinguish their surviving
auxiliary-output/conversion paths from removed kicker-strategy logic. The 4EF2
initialization read still seeds 0885, but that old follower threshold has no
replacement-controller consumer and is excluded from the definition. Conversions on those inherited
controls are retained, not newly established units. The resident low-TPS
spark option at 4E90.1 is still tested, but the normal request writer at
0036.5 was removed with the old strategy; it is not offered as an operative
tuning switch. Its surviving read and omitted write roles remain distinct.

Both maintained non-OEM workbooks now describe this actual candidate. Original
OEM role columns, unrelated tabs and the two OEM workbooks are preserved.
Omitted operational roles remain listed even where reset clearing survives;
specific replacement cleanup is identified separately. Writer evidence carries
the new image identity, current fixed writers and qualified surviving indexed
writers. It is not an exhaustive dynamic pointer-write proof.

## Validation and reproduction

```sh
python tools/build_manual_idle_release.py /path/to/RevA.bin --output /path/to/revb
python tools/verify_manual_idle_release.py /path/to/RevA.bin /path/to/revb/0.3.12_engine_only_manual_idle_revB.bin --output /path/to/runtime.json
python tools/verify_manual_idle.py --check-recorded
python -m unittest discover -s tests -p 'test_manual_idle*.py' -v
python tools/build_custom_xdf.py --check
python tools/verify_custom_xdf.py --rom /path/to/revb/0.3.12_engine_only_manual_idle_revB.bin
python -m unittest discover -s tests -p test_custom_xdf.py -v
```

The builder verifies the exact baseline, bounds all 4,271 changed bytes to
reviewed allocations, repairs the checksum and reverses every span back to
the exact input. Its patch manifest records all before/after bytes and all
27 spark cells. Whole-root direct CFG covers 6,449 instruction starts and
rejects execution into erased strategy/data bytes, direct gear selectors,
old Drive-bank references and recovery-calibration references. Indexed and
external frontiers remain explicit limits.

The original controller suite makes 2,943 native-C/HC11 comparisons, covering
all 266 idle instructions. Four new HC11 gate tests cover 598 fixtures:
active-DFCO byte arithmetic, fuel return, idle threshold equality, saturation,
stale flags and startup-word preservation. Eight XDF tests cover deterministic
generation, protected addresses, conversions and reversible edits.

Nine full-reset scenarios execute the actual candidate bytes, including
320-call hot/cold runs. All reach the scheduler and fuel/spark/IAC paths with
valid checksum and no retired-code execution. Retired-state noise leaves the
hot fixture's engine-output digest unchanged. Maximum observed IAC call is
1,359 modeled cycles; this is not a worst-case hardware deadline bound.

The simulator imposes RPM and models devices. These checks establish software
behavior, not engine-response stability, mixture, physical airflow, motor
motion or actual PCM timing. Native TunerPro GUI loading has not been tested
here. Start a new log series for this controller; the exact Rev A rollback
pair is supplied alongside it.
