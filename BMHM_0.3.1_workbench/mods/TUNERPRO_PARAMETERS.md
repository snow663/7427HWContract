# TunerPro parameters for BMHM 0.3.1

## Flags

### Force Open Loop At Idle

- Address: `$FE9F`
- Bit: 0
- Mask: `$01`
- 0: stock closed-loop-idle behavior permitted.
- 1: force open-loop fuel and disable BLM learning while `$0050.b7` idle is active.

### Disable Closed Loop Fueling

- Address: `$FE9F`
- Bit: 1
- Mask: `$02`
- 0: normal `$31` closed-loop operation, subject to bit0.
- 1: globally block closed-loop O2 fuel correction, neutralize BLM application to 128, and force INT/P signed PW correction to zero.

`$FE9F bit2` is **not used**. Remove/ignore the retired "Disable VSS Input" definition from the rejected VSS-zero experiment.

## Scalars

### True Idle Control Enter RPM

- Address: `$FF88`
- Size: 1 byte
- Equation: `X * 25`
- Units: RPM
- 0.3.1 default: 1100 RPM (`$2C`).

### True Idle Control Exit RPM

- Address: `$FF89`
- Size: 1 byte
- Equation: `X * 25`
- Units: RPM
- 0.3.1 default: 1200 RPM (`$30`).

The enter value should remain below the exit value to preserve hysteresis.

## Option-byte values

- `$FE9F=$00`: normal closed-loop including idle.
- `$FE9F=$01`: open-loop at idle only (0.3.1 default).
- `$FE9F=$02`: global closed-loop fuel disable.
- `$FE9F=$03`: global closed-loop fuel disable; bit0 becomes functionally redundant.

Any saved BIN edit changes the `$31` checksum; recalculate `$4006-$4007` before programming persistent memory.
