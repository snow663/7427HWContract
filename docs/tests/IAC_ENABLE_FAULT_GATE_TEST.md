# IAC Enable / Fault Gate Test

## Goal

Bench-prove the IAC Enable candidate path:

```text
L000A bit4
-> L004C bit4
-> L3062 bit4 candidate
-> physical IAC driver Enable candidate
```

This test only covers Enable/fault behavior. A/B phase order and park/reset movement are separate contracts.

## Required Signals / Trace Values

- physical IAC Enable candidate
- physical IAC A candidate
- physical IAC B candidate
- `L000A bit4`
- `L004C bit4`
- `L3062 bit4` if bus trace is available
- `L00A7` battery volts, VDC/10
- `L003E bit2` low-battery/protection flag
- `L0044 bit4` ignition-off/startup/shutdown candidate
- `L0004 bit3` bad-shutdown candidate
- `L0009 bit0` IAC reset-in-work gate
- `L0007/L0008` desired/actual state for no-step versus step behavior

## Static Source Candidate

```text
0x91A5  LDAA L00A7       ; BAT VOLTS, VDC/10
0x91A7  CMPA #169        ; 16.9 VDC high threshold candidate
0x91AB  ANDB #$EF        ; clear bit4 candidate

0x91B3  CMPA L4EB6       ; low threshold candidate
0x91B8  BSET L003E,#$04  ; low-battery/protection flag

0x91BD  BCLR L003E,#$04
0x91C0  ORAB #$10        ; set bit4 candidate

0x9200  STAB L000A
0x920A  STAA L004C
0xF411  STAA L3062
```

## Test Matrix

| Test | Condition | Expected if source model is correct |
|---|---|---|
| normal key-on/run voltage | `L00A7` in valid range | `L000A/L004C/L3062 bit4` set; physical Enable asserts if mapping is correct |
| desired == actual | no A/B step demand | Enable remains asserted after voltage gate passes |
| desired != actual | A/B stepping | Enable remains asserted while A/B phase changes |
| high-voltage threshold | safely force/simulate `L00A7 > 169` | bit4 clears and/or physical Enable deasserts; low-battery/protection flag path sets |
| low-voltage threshold | safely force/simulate `L00A7 <= L4EB6` | `L003E bit2` sets; `ORAB #$10` skipped; Enable state classified |
| bad-shutdown setup | force/observe `L0004 bit3` path | `L93C5` clears bit4 if `L0009 bit0` is clear |
| reset in work | `L0009 bit0` set | `L93C5` setup clear is skipped |
| forced bit4 clear | force `L000A bit4=0` with A/B changing | classify whether driver motion is inhibited |

## Data Capture Table

```csv
test_name,event_index,l00a7_batt_vdc10,l4eb6_threshold,l003e,l0044,l0004,l0009,l000a_before,l000a_after,l004c_before,l004c_after,l3062_write,physical_enable,a_state,b_state,l0007,l0008,path_result,notes
```

## Enable Classification

```text
EN-A:
  bit4 is confirmed physical IAC Enable and is normally held asserted.

EN-B:
  bit4 is a driver power/health gate but not direct Enable pin.

EN-C:
  bit4 is refreshed as part of output latch but does not independently gate IAC motion.

EN-D:
  Enable behavior is fault/test/reset-only after startup.

EN-E:
  static interpretation incomplete.
```

## Voltage/Fault Classification

```text
VOLT-A:
  L00A7/#169/L4EB6 are true battery/driver voltage gates for IAC Enable.

VOLT-B:
  voltage gates set flags but do not physically deassert Enable.

VOLT-C:
  high/low voltage gates affect stepping cadence or direction rather than Enable.

FAULT-A:
  bad-shutdown/setup path clears physical Enable.

FAULT-B:
  bad-shutdown/setup path clears only software mode state.
```

## Pass Criteria

```text
PASS:
  L00A7 is confirmed as the value controlling the voltage gate.
  #169 high threshold behavior is observed or safely simulated.
  L4EB6 low threshold behavior is observed or safely simulated.
  L000A bit4 propagates to L004C bit4 and L3062 bit4.
  physical Enable pin mapping is classified.
  Enable stays asserted during normal no-step and step behavior if EN-A is true.
```

## Fail / Rework Criteria

```text
REWORK:
  physical Enable does not correlate with L000A/L004C/L3062 bit4.
  A different bit controls the physical Enable pin.
  voltage gating does not affect bit4 or related IAC behavior.
  bit4 is actually a phase, test, or unrelated output bit.
  external driver fault behavior dominates over CPU-visible bit4 state.
```

## Next Contract

After Enable/fault behavior is split, continue with:

```text
IAC_INIT_PARK_CONTRACT
```
