# BMHM 0.3.3 — startup fast-idle governor

Experimental successor to BMHM 0.3.2. This build retains the Bosch/Motronic-style state layer and adds a distinct STARTUP FAST IDLE state so the stock coolant-based IAC cold offset no longer has unlimited authority over engine speed.

## Binary identity

- File: `BMHM_0.3.3.bin`
- Base: `BMHM_0.3.2.bin`
- SHA-256: `08c61b87013ade0c226e5edaea36a9b11874d73f62e74365d187f6fd625c2040`
- `$31` checksum: `$3D88` at `$4006-$4007`

The binary itself is distributed separately from this workbench documentation.

## Why this change was made

The 2026-08-24 cold-start log began at about 35.8 C coolant with desired idle near 887 RPM, actual speed around 1675-1700 RPM, and both present and desired IAC position at 112 steps. Closed-loop IAC was disabled. The engine followed the slowly decaying startup/cold-air offset rather than a controlled RPM target.

The source trace shows three distinct startup-air/RPM mechanisms:

1. `$4EB8 -> L086B`: short after-start airflow term, initialized at `$9429`, decayed at `$A2DA-$A2F7`.
2. `$4F6E -> L085C`: short startup desired-RPM adder, initialized at `$9455`, decayed at `$A2FA-$A327`.
3. `$4EC2/$4ECF -> L02A3/L02AD`: long-lived coolant-based IAC cold offset, initialized at `$94B5-$94D2` and maintained/decayed at `$9FE9-$A069`.

At 27 seconds run time, the first two short startup terms should already be largely or fully gone. The long-lived cold offset is the dominant remaining authority.

## Stock IAC closed-loop startup delay

`$4EF5-$4F01` and `$4F02-$4F0E` are the RPM-high and RPM-low IAC closed-loop enable-delay tables. Source scale is `X * 10 seconds`.

Stock/current 0.3.2 values were `10` at every coolant node, i.e. a 100-second startup delay.

BMHM 0.3.3 changes both tables to `1` everywhere, i.e. 10 seconds.

The existing `$4EF4` post-qualification delay remains intact.

## STARTUP FAST IDLE state

The new mode is deliberately separate from TRUE IDLE.

STARTUP FAST IDLE is eligible when:

- the stock corrected-TPS IAC qualification at `$99E2` passes;
- the startup fast-idle cancellation latch has not been set; and
- either cold-offset accumulator (`L02A3` or `L02AD`) is still materially nonzero.

When eligible:

- a coolant-based fast-idle RPM target is loaded into `L0857`;
- the stock IAC closed-loop controller is allowed to run after the shortened startup delay;
- TRUE-IDLE state is not required.

This lets the stock feedback IAC controller subtract enough airflow to hold a defined cold RPM even while the cold-offset reserve remains active.

## Fast-idle target table

New table: `$FF60-$FF6C`, 13 bytes, `RPM = X * 12.5`.

It uses the same fixed coolant nodes as the stock cold-offset tables:

| Coolant C | Target RPM |
|---:|---:|
| -28 | 1400 |
| -16 | 1400 |
| -4 | 1375 |
| 8 | 1350 |
| 20 | 1300 |
| 32 | 1250 |
| 44 | 1175 |
| 56 | 1100 |
| 68 | 1000 |
| 80 | 900 |
| 92 | 850 |
| 104 | 850 |
| 116 | 850 |

At the approximately 35.8 C condition from the cold-start log, interpolation should command roughly 1225 RPM rather than allowing the former ~1700 RPM open-loop result.

## First-throttle cancellation latch

`L0009.b1` is repurposed.

Stock meaning: first-drive-away IAC kickdown latch.

The no-VSS work already bypassed the VSS-dependent drive-away kickdown consumer, and the complete 0.3.2 drive log showed this bit remained `Not Set` for all 3502 samples. It is therefore available as a startup-state latch without allocating new RAM.

New meaning:

- `0`: STARTUP FAST IDLE still eligible
- `1`: STARTUP FAST IDLE cancelled for the current engine run

The stock startup initialization at `$94B2` still clears it.

The prior `$9EA7 -> $9ECA` VSS bypass is replaced with `$9EA7 -> $FEA0`. The new routine compares corrected TPS `$01D9` to the virtual closed-throttle exit threshold `$FF8B`. On the first genuine throttle opening, it sets `L0009.b1`. `$9EA3` already skips the drive-away block once this bit is set.

This is important because it prevents the cold-offset accumulator from reactivating FAST IDLE during later closed-throttle deceleration.

## IAC qualification hook

`$99F2-$99F9` now jumps to `$FF20`.

Logic:

```text
if startup fast idle not cancelled
   and cold offset still active:
       load coolant fast-idle target
       qualify stock IAC closed-loop path
else if TRUE_IDLE ($0050.b7):
       qualify stock IAC closed-loop path
else:
       use stock no-qualification path
```

The normal corrected-TPS qualification at `$99E2` remains immediately upstream.

## Idle spark

The 0.3.2 TRUE-IDLE spark gate is behaviorally unchanged. It was moved from `$FF30` to `$FED3` only to free contiguous cave space for the new FAST-IDLE IAC routine.

FAST IDLE does not automatically enable TRUE-IDLE spark. Until the normal TRUE-IDLE state is entered, startup speed is controlled primarily by IAC airflow while spark remains on the non-idle path.

## 0.3.2 drive validation before adding FAST IDLE

The 2026-08-24 16:32 drive log validates the central state layer:

- closed corrected TPS (`<=1.2%` logged), RPM >=1225: 293 samples; Idle Flag ON = 0/293; idle spark ON = 0/293; IAC closed loop enabled = 0/293; BLM cell 16 = 0/293.
- closed corrected TPS, 700-1100 RPM: 477 samples; Idle Flag ON = 473/477; idle spark ON = 473/477; BLM cell 16 = 474/477; fuel open loop = 474/477; IAC closed loop enabled = 459/477.

The few one-frame mismatches are consistent with the known non-atomic ALDL serialization skew. The actual DECEL -> TRUE-IDLE state transition is therefore behaving as designed.

The same log also confirms that the former VSS drive-away latch remained `Not Set` for the entire run, which is why `L0009.b1` is reused here.

## Lambda observation from the 0.3.2 drive log

DAMP1 itself was not changed in 0.3.2, but this particular drive was more lean-biased than the previous 0.3.1 validation in the comparable clean closed-loop region (PE/AE/DFCO excluded, TPS >2.5%, 1200-3200 RPM, 50-100 kPa):

- INT mean: 131.66
- INT median: 130
- mean `abs(INT-128)`: 6.38 counts
- BLM mean: 129.36
- slow-rich occupancy: 43.1%
- raw O2 mean: ~438 mV

Because the controller gains were unchanged, this is evidence that the base fuel/learned cells in the exercised region were leaner in that run, not evidence that the DAMP1 gain reduction stopped working. Higher-load cells 10 and 13 carried the largest positive INT/BLM corrections.

## Validation target for 0.3.3

On a similar 30-45 C cold start:

1. initial flare may still occur;
2. after roughly 10 seconds, RPM closed loop should be allowed to enable while TPS remains closed;
3. Desired Idle RPM should rise to the new fast-idle target, roughly 1200-1250 RPM at that coolant;
4. IAC steps should retract from the previous 112-step plateau;
5. actual RPM should settle near the fast-idle target;
6. the ALDL field formerly named `1st Drive Away flag for IAC Kickdown` should set on the first real throttle opening;
7. once set, later closed-throttle decel must remain pure DECEL/TRUE-IDLE behavior and must not re-enter STARTUP FAST IDLE.
