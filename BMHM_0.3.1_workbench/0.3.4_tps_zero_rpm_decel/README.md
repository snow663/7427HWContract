# BMHM 0.3.4 — TPS self-zero uses engine decel, not VSS

Experimental successor to BMHM 0.3.3. This revision removes the specifically traced filtered-VSS dependency from the runtime **upward TPS self-zero learner** while preserving the stock learned-baseline behavior.

## Binary identity

- File: `BMHM_0.3.4.bin`
- Base: `BMHM_0.3.3.bin`
- Base SHA-256: `08c61b87013ade0c226e5edaea36a9b11874d73f62e74365d187f6fd625c2040`
- SHA-256: `e024b988bd0b47b0399d772a5a655b7a4a0d7eed9d27eb7966739ecb1875c73f`
- `$31` checksum: `$3C9E` at `$4006-$4007`

The binary itself is distributed separately from this workbench documentation.

## Change

The stock TPS self-zero learner around `$B12C-$B15D` used a filtered vehicle-speed decrease to decide when one upward learned-zero correction was safe.

0.3.4 preserves the stock event/latch algorithm but changes its deceleration source:

```text
stock:
    previous filtered VSS L00F7
      - current filtered VSS L00D7

0.3.4:
    previous RPM reference L00F7
      - current engine RPM/25 L0062
```

Only two operands change:

- `$B12F: D7 -> 62` — `SUBA L00D7` becomes `SUBA L0062`
- `$B161: D7 -> 62` — `LDAA L00D7` becomes `LDAA L0062`

No code cave and no new RAM are required.

## Deceleration threshold

`$5B2A` remains raw `10`.

Because `$0062` is RPM/25, the existing threshold now means:

```text
10 * 25 = 250 RPM cumulative drop
```

The stock accumulation behavior is retained: while the drop is below threshold, the reference is not updated, so the decrease accumulates. Once the event qualifies, the learner can move the TPS zero upward by the existing `$5B29 = 1` A/D count and then latches the event until RPM rises again.

## What stays stock

- raw TPS acquisition at `$00A6`
- learned zero at `$02F6`
- downward zero tracking at `$B11D-$B129`
- initialization/startup TPS-zero filtering
- `$5B29` one-count upward increment
- `$5B24` learned-zero clamp
- stock diagnostic/brake-related qualifiers in the upward-learn path
- final corrected TPS calculation through `$01A6/$01D9`

## Why this fits the 0.3.x architecture

The learner only needs a credible **engine deceleration event** to decide that a small upward TPS-baseline correction is appropriate. It does not need road speed. Using RPM keeps throttle adaptation in the engine-state domain and prevents phantom VSS spikes from indirectly moving the corrected TPS baseline.

## 0.3.3 features retained

0.3.4 otherwise carries 0.3.3 unchanged, including:

- DAMP1 narrowband closed-loop damping
- Bosch-style PART / DECEL / TRUE-IDLE state layer
- corrected-TPS virtual idle switch
- closed-throttle open-loop policy
- startup FAST-IDLE governor and coolant RPM target
- first-throttle FAST-IDLE cancellation latch
- consumer-level VSS authority removal

## Last drive-log decision

The 2026-08-24 `20:09:37` drive log was centered well enough in the dominant highway cruise region that no VE or O2-gain changes are bundled into 0.3.4. In the dominant cell-6 cruise region (~2400-3300 RPM, 30-50 kPa), mean INT was about 127.4, mean BLM about 127.6, and the combined correction was about -0.8%.

Keeping 0.3.4 architecture-only makes the next cold-start/drive log easier to interpret.