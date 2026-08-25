# BMHM 0.3.4 validation — 2026-08-25 cold start / short drive

Log: `2026-08-25_15.25.47.csv`

## Cold-start result

The log begins before cranking and captures the full start from about 31.2 C coolant.

The 0.3.3 fast-idle target table is visible in the ALDL `Desired Idle RPM` item. Around 31-32 C it repeatedly reports 1250 RPM, then walks down with coolant approximately as intended. However, the target is not yet controlling engine speed tightly:

- initial flare reaches about 1700-1725 RPM
- at 35.8 C: ~1625 RPM, IAC ~99, fast target ~1225 RPM
- at 40 C: ~1450 RPM, IAC ~92, fast target ~1200 RPM
- at 44 C: ~1425 RPM, IAC ~84-85, fast target ~1175 RPM
- at 56 C: ~1200-1225 RPM, IAC ~63-64, fast target ~1100 RPM

Compared at similar coolant to the 2026-08-24 pre-governor cold log, the new build reduces speed by roughly 75 RPM around 36-40 C and retracts the IAC by about 8-13 steps, but the engine still runs several hundred RPM above the desired fast-idle target early in warmup.

RPM closed-loop becomes enabled during startup while TRUE-IDLE remains off, so the new FAST-IDLE state gate itself is functioning. The first real throttle opening occurs at about 503 seconds engine run time and the repurposed `1st Drive Away flag for IAC Kickdown` latches Set and remains set through the short drive, confirming startup FAST-IDLE cancellation behavior.

## Ordering discovery

The log repeatedly alternates `Desired Idle RPM` between the FAST-IDLE target and the stock warm-idle value (often 887 RPM). Source order explains this.

The main IAC loop computes RPM error at:

- `$96F0`: `LDAA L0063` (RPM/12.5)
- `$96F2`: `SUBA L0857` (desired idle RPM/12.5)
- `$96FE`: stores absolute RPM error in `L0858`

BMHM 0.3.3/0.3.4 currently writes the FAST-IDLE target into `L0857` from the IAC qualification hook at `$99F2 -> $FF20`, which is downstream of the `$96F0-$96FE` RPM-error computation in the IAC pass.

Stock desired-idle generation is performed by `$989C-$99A8`, and `$9EA0` calls `$989C` during IAC housekeeping. Consequently, `L0857` is being written by both the stock desired-RPM path and the FAST-IDLE helper at different phases. ALDL can therefore sample either value. More importantly, the FAST-IDLE target is not guaranteed to be the value used when the controller computes RPM error.

The next revision should move the FAST-IDLE target override immediately after stock desired-RPM generation, rather than writing it from the qualification hook.

## Remaining airflow-floor problem

Even with RPM closed-loop enabled, IAC desired/present position remains high and largely follows the slow cold-offset decay. This indicates that the GM coolant cold-offset airflow remains an additive floor that the normal integral controller cannot fully cancel.

A Bosch-style next step should treat coolant cold-start air as feed-forward with explicit authority limits, rather than allowing the raw cold-offset term to dominate the final IAC command. Candidate implementation: startup-only coolant-based maximum IAC position or an overspeed-driven decay of the cold-offset accumulator, bounded by the FAST-IDLE state and cancelled on the first real throttle opening.

## Bosch state validation on the short drive

After the first throttle opening, FAST-IDLE remains latched off. In the available short drive segment:

- closed TPS at >=1225 RPM: Idle Flag OFF, IAC CL OFF, idle spark OFF, BLM cell 16 not forced
- closed TPS <=1100 RPM: Idle Flag ON, IAC CL enabled about 96%, idle spark ON, BLM cell 16

So the DECEL / TRUE-IDLE split from 0.3.2 remains intact after the 0.3.3 and 0.3.4 changes.

## TPS-zero / VSS validation

PCM VSS stayed at 0 for this entire log, so this run does not exercise the 0.3.4 RPM-decel replacement under phantom-VSS conditions. Corrected closed TPS remains near 0%, but a later run with phantom VSS activity would be a stronger test.

## Lambda snapshot

The post-warmup drive is short and follows a PCM reset, so BLM remains 128 throughout. In the available clean part-load closed-loop samples, INT averages about 128.48. This is not enough duration to re-evaluate long-term BLM centering, but it shows no immediate closed-loop control problem.
