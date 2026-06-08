# Spark BYPASS / EST Transition Test

## Goal

Determine when the PCM transfers spark authority from module bypass/base timing to EST/ASIC-controlled timing.

## Required Signals

- REF input
- EST output
- bypass wire/state
- RPM/ref simulator state
- `L004F`
- `L0044`
- `L0210`
- `L022C`
- `L3FCA`
- `L0205`
- `$3FEC`
- `$3FE4`
- `$3FE6`
- `$3FE8`
- `$3FF6`
- `$3FDC`
- Error 42 / EST monitor status if visible

Watched but not currently primary in the captured static EST monitor rows:

- `L022B`
- `L0204`

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| key-on/no-ref | no RPM | bypass safe, no EST authority |
| crank below threshold | low ref rate | bypass/startup behavior |
| crank above run threshold | crosses RPM gate | EST authority transfer candidate |
| first 1 DRP only | insufficient events | no EST handoff if DRP count gate exists |
| first 2 DRPs | run qualification candidate | run/EST enable if gate exists |
| missing bypass/EST response | simulated mismatch | Error 42 counter behavior |
| forced bad rolling state | corrupt `$3FF6/$3FDC` | determine whether bypass protects first event |
| hot restart | normal restart | repeatable authority transition |
| skip `$3FEC->$3FE4` | fixed run state | determine if mirror/ack participates in authority/monitoring |
| force `L004F bit6` clear | running | determine if EST monitor only or authority-affecting |
| force `L004F bit7` clear | running | determine if engine-running gate suppresses run spark authority |

## Classifications

```text
BYP-A:
  bypass/EST transfer is gated by RPM threshold only.

BYP-B:
  transfer requires RPM threshold plus DRP/ref event count.

BYP-C:
  transfer requires ASIC status/mirror handshake.

BYP-D:
  LA906 can run before EST authority but does not affect coil until bypass transfer.

BYP-E:
  Error 42 monitor depends on $3FCA/L0205/L022C behavior.

BYP-F:
  static interpretation incomplete.
```

## Procedure

1. Capture key-on/no-ref state after global clears.
2. Begin crank simulation below the 450 RPM candidate threshold.
3. Record bypass wire/state, EST output, `L004F`, `L0044`, `L0210`, `L3FCA`, `L0205`, `$3FF6`, and `$3FDC`.
4. Increase ref rate through the threshold and capture the first set of qualifying DRP/ref events.
5. Determine when `L004F bit7` is set and when startup spark `L01F2` is cleared.
6. Determine whether `$3FE8/$3FE6` writes occur before coil authority changes at the bypass/EST output.
7. Compare EST output timing before and after authority transfer.
8. Force bad `$3FF6/$3FDC` before first LA906 and observe whether bypass/module authority prevents a wild coil event.
9. Simulate EST mismatch or frozen `$3FCA/L0205` delta and observe `L022C` Error 42 counter behavior.
10. Skip or freeze `$3FEC->$3FE4` mirror and observe authority transfer, EST output, and Error 42 monitor behavior.
11. Repeat as hot restart.

## Data To Record

```csv
test_name,event_index,ref_state,rpm_ref_hz,bypass_state,est_output_state,l004f,l0044,l0210,l3fca,l0205,l022c,l3fec,l3fe4,l3fe8,l3fe6,l3ff6,l3fdc,error42_state,la906_seen,path_result,notes
```

## Pass Criteria

```text
BYP-B pass:
  L004F bit7 engine-running is set only after RPM threshold and DRP/ref count qualification.

BYP-D pass:
  LA906 writes occur before physical EST authority, but coil timing remains module/base/bypass until authority transfer.

BYP-E pass:
  Error 42 monitor behavior follows L3FCA/L0205 sample comparison and L022C counter increment/clear behavior.

BYP-C pass:
  skipping $3FEC->$3FE4 mirror blocks authority transfer, causes monitor failure, or prevents stable subsequent EST behavior.
```

## Fail / Stop Conditions

Stop and preserve trace if:

- `$3FE8/$3FE6` affect the coil before any valid run/authority gate.
- bad `$3FF6/$3FDC` seeds produce a wild first spark event.
- `L004F bit6` directly changes physical bypass/EST authority rather than only the monitor gate.
- Error 42 activity follows `L022B/L0204` instead of the captured `L022C/L0205` path.
- `$3FEC->$3FE4` is unrelated and another untracked register performs the authority handshake.

## Expected Minimal-OS Split

If the static model holds, future spark code should split authority transfer from timing math:

```text
SPARK_BYPASS_INIT:
  keep module/base timing safe during key-on and crank

SPARK_RUN_QUALIFY:
  require valid DRP/ref period, RPM threshold, and DRP/ref count gate

SPARK_ENABLE_EST_AUTHORITY:
  permit ASIC/EST timing only after safe state exists

SPARK_FAULT_MONITOR:
  decide whether to retain, simplify, or disable stock Error 42 behavior
```

Timing math and handoff remain separate:

```text
SPARK_CONVERT
SPARK_ROLLING_UPDATE
SPARK_ASIC_HANDOFF
```

## Next Step

If Error 42 behavior remains complex after bench/static review, create:

```text
docs/contracts/SPARK_EST_FAULT_MONITOR_CONTRACT.md
maps/contracts/spark_est_fault_monitor_contract.csv
docs/tests/SPARK_EST_FAULT_MONITOR_TEST.md
```

If authority transfer is clear enough, create:

```text
docs/contracts/SPARK_MINIMAL_MODULE_BOUNDARY.md
```

Still no `SPARK_WRITE` until authority transfer, fault handling, and the LA906 output effect are bench-classified.
