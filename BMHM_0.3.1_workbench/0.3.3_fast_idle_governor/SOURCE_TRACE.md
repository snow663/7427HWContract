# Source trace — cold-start IAC / fast-idle authority

This trace is from the BMHM/HAC `$31` source and is the authority for the BMHM 0.3.3 startup fast-idle patch.

## Startup initialization

### IAC closed-loop startup delays

`$9411-$9426`

```text
$9411  LDAA L0283
$9414  LDX  #$4EF5
$9417  JSR  $F4C1
$941A  STAA L0866

$941D  LDAA L0283
$9420  LDX  #$4F02
$9423  JSR  $F4C1
$9426  STAA L0867
```

Source comments identify `$4EF5-$4F01` and `$4F02-$4F0E` as coolant-indexed IAC closed-loop enable delays after startup, scale `X * 10 seconds`. BMHM values are 10 at every node, i.e. 100 seconds.

The runtime decrement is at `$A288-$A297`.

## Short after-start airflow

`$9429-$9432`

```text
$9429  LDAA $4EB8
$942C  STAA L086B
$942F  LDAA $4EB9
$9432  STAA L086C
```

`$4EB8 = 60` is source-commented as about 23% flow added after startup. `$4EB9 = 1` controls its decay period.

Runtime decay is `$A2DA-$A2F7`:

```text
$A2DA  LDAA L086B
...
$A2E6  LDAB L086C
...
$A2F0  LDAB $4EB9
$A2F3  STAB L086C
$A2F6  DECA
$A2F7  STAA L086B
```

This term also feeds IAC airflow before the flow-to-step conversion, e.g. `$9787 ADDA L086B`.

## Short startup desired-RPM adder

At startup `$9455-$945B` looks up `$4F6E` and stores the result in `L085C`.

`$9473-$947C` initializes its decay timing from `$4EBB` and `$4EBA`.

Runtime decay is `$A2FA-$A327`.

The desired-idle calculation uses `L085C` around `$993D-$994F`.

## Long-lived coolant cold offset

### Initialization

Drive offset:

```text
$94B5  LDAA L0283
$94B8  LDX  #$4ECF
$94BB  JSR  $F4C1
$94BF  STD  L02AD
$94C2  STD  L02AF
```

Park/Neutral offset:

```text
$94C5  LDAA L0283
$94C8  LDX  #$4EC2
$94CB  JSR  $F4C1
$94CF  STD  L02A3
$94D2  STD  L02A5
```

The same startup block loads the cold-offset delay from `$4EDC` into `L0875` at `$94D5-$94DE`.

### Runtime decay

`$9FE9-$A069` houses the long-lived cold-offset housekeeping.

Key points:

- `L0875` is the delay timer.
- `$4EBD` is the maximum-offset decay multiplier.
- `$4EBE` applies the Park/Neutral decay multiplier to `L02A3`.
- `$4EBF` applies the Drive decay multiplier to `L02AD`.
- `$4EDC` is looked up again by coolant at `$A049-$A04F`.
- `$4EE9` is an airflow-dependent multiplier used to rebuild the delay at `$A053-$A069`.

This is the term still materially present tens to hundreds of seconds into the 2026-08-24 cold-start log.

## IAC flow-to-step conversion

The IAC airflow command eventually passes through `$9883-$9899`:

```text
$9883  LDX #$4E92
...
$9891  LDD 0,X
...
$9899  STAA L0008
```

`$4E92` is the stock IAC step-position versus desired-airflow linearization table.

## Desired idle calculation

`$98A3-$99A8` calculates `L0857` desired idle RPM/12.5 from the coolant idle-RPM tables plus battery, rough-idle and other compensation.

The final store is:

```text
$99A8  STAA L0857
```

BMHM 0.3.3 does not replace that normal calculation globally. It overrides `L0857` with the new `$FF60` fast-idle table only while STARTUP FAST IDLE is eligible.

## Stock closed-loop IAC qualification

The original path begins at `$99E2`:

```text
$99E2  LDAA L01D9
$99E5  CMPA $4EF2
$99E8  BCS  $99EF
...
$99F2  LDAA L0284
$99F5  CMPA $4EF3
$99F8  BCS  $9A05
$99FA  ... no-qualification path
$9A05  BSET L0036,#$04
```

The 0.3.x no-VSS work removed VSS authority here. BMHM 0.3.2 then required centralized TRUE IDLE at `$99F2`, which meant the feedback IAC controller could not help while cold-start RPM remained above the 1100/1200 true-idle window.

## Stock startup-delay use

After IAC qualifications are accepted, `$9A10-$9A3C` uses startup delay variables `L0866/L0867` before the actual closed-loop idle controller is allowed to proceed.

The code also uses `L0036.b7` (`IDLE RPM TOO HIGH`) to distinguish high/low RPM error. That bit is formed at `$96F0-$96FE` by comparing actual RPM/12.5 (`L0063`) against desired idle RPM/12.5 (`L0857`).

This confirms that the stock IAC feedback controller already has explicit high-RPM and low-RPM control paths. BMHM 0.3.3 reuses that existing controller rather than inventing a separate stepper governor.

## BMHM 0.3.3 implementation addresses

- `$99F2 -> $FF20`: FAST-IDLE / TRUE-IDLE IAC qualification gate.
- `$9EA7 -> $FEA0`: first-throttle cancellation-latch handler.
- `$A85A -> $FED3`: relocated TRUE-IDLE spark gate; behavior unchanged.
- `$FEA0-$FEAD`: corrected-TPS startup cancellation routine.
- `$FEB0-$FEBC`: coolant fast-idle target lookup and `L0857` store.
- `$FED3-$FEDC`: relocated TRUE-IDLE spark gate.
- `$FF20-$FF3B`: IAC state gate.
- `$FF60-$FF6C`: 13-point fast-idle RPM table.
- `$4EF5-$4F01`: startup IAC CL high-RPM delay, 100 s -> 10 s.
- `$4F02-$4F0E`: startup IAC CL low-RPM delay, 100 s -> 10 s.

## Why the startup latch uses L0009.b1

Stock `$94B2` clears `L0009.b1` at startup. Stock `$9EA3/$9EC7` used it as a first-drive-away cold-offset kickdown latch qualified by VSS.

The consumer-level no-VSS patch bypassed the speed-based kickdown at `$9EA7`, leaving the bit unused. The 0.3.2 drive log confirms the ALDL representation of this flag remained `Not Set` for all 3502 samples.

BMHM 0.3.3 therefore repurposes the same initialized RAM bit as a first-throttle cancellation latch. This provides startup/decel history without inventing new RAM ownership.
