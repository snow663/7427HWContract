# Preserved GM Output-Driver Islands

## Decision

For the retained `$31` BMHM engine-control scope, the replacement OS will preserve the proven GM software-to-hardware command behavior instead of requiring full electrical characterization before first engine operation.

Architecture:

```text
custom control algorithms
→ clean semantic requests
→ compatibility adapter
→ preserved GM output-driver island
→ 7427 hardware
```

The electrical meaning after the preserved software command boundary is deliberately deferred. Connector polarity, transistor topology, current, and ASIC internal implementation are not prerequisites for this route.

## Scope rule

Only hardware required by the first engine-running configuration is retained now:

```text
fuel synchronous output
fuel asynchronous/AE pulse output
IAC stepper output
spark/EST handoff
fuel-pump relay output
```

MIL and all unused transmission/emissions/auxiliary I/O are deferred. They may be characterized and added later without reopening the engine-control extraction phase.

## Fuel island

### Production TBI mode proof

BMHM `$400B = $04`; bit 0 is clear. Therefore the normal TBI path at `850B-8515` takes:

```text
L0250 final BPW
→ STD $3FCE
```

The CPI/PFI delayed-injection branch at `8517+` is not selected by BMHM and is outside the first retained configuration.

Stock no-fuel behavior also explicitly writes zero to `$3FCE` at `8424-8429`.

### Synchronous ABI

```text
input: 16-bit final injector pulse-width count in the stock $3FCE command units
zero: no synchronous injector pulse intent
output command: $3FCE
```

The custom fuel algorithm owns all fueling mathematics and may directly produce the final stock-compatible count. It does not need to reproduce the upstream stock RAM layout.

### Asynchronous / AE ABI

The stock async pulse service at `L8548` ultimately uses:

```text
final async pulse count → $3FF2
$3FFC bit-2 clear/write → set/write trigger sequence
```

with the stock very-short `JSR LF3ED` delays between hardware accesses. `LF3ED` itself is an `RTS`; the delay is the call/return instruction time.

For the clean OS, low-PW compensation and biasing remain algorithm/adapter responsibilities. The preserved hardware island consumes a final async pulse count and reproduces only the `$3FF2/$3FFC` command sequence.

### Deferred fuel machinery

TOC4/TOC5 scheduler machinery remains available as historical/static fallback but is not on the critical path for BMHM TBI when the `$3FCE` synchronous command and `$3FF2/$3FFC` async trigger paths are preserved.

## IAC island

Stock output-driver behavior is `L91C2-L920D` plus the output-shadow copy at `F40F-F411`.

Compatibility ABI:

```text
input: desired IAC position/count
private driver state:
  current software position
  direction bit
  A/B phase bits
  enable bit
output byte:
  stock IAC bits merged into the port-D shadow
  shadow copied to $3062
```

Required behavior preserved:

1. Compare actual software position against desired position.
2. If direction must reverse, change the direction bit without changing position (`zero-step reversal`).
3. Otherwise increment/decrement software position by one count.
4. Advance the original A/B phase ring exactly as `91E8-91FE` does.
5. Merge only bits `$1C` into the output shadow using stock mask `$E3`.
6. Commit the resulting shadow byte to `$3062`.

The original battery/ignition qualification does not need to live inside the driver island. The clean OS permission layer owns whether IAC motion is allowed. When permission is absent, the compatibility layer uses the stock disable semantic: clear the driver enable bit rather than inventing physical polarity.

## Fuel-pump island

Stock behavior provides a direct software command:

```text
$FF → $306F : pump relay command asserted
$00 → $306F : pump relay command cleared
```

Evidence:

- startup/ref path `7516-7518` writes `$FF` to `$306F`
- pump timeout path `A5A9-A5AA` writes `$00` to `$306F`

Prime duration, crank/run qualification, stall handling, and shutdown timing remain clean lifecycle logic. The preserved island only commits the stock byte command.

## Spark / EST island

The preserved spark boundary is the existing final conversion/rolling handoff path beginning at `AB41` and the hardware write sequence at `ABA2-ABC8`.

The compatibility input is the final signed spark command in the same stock semantic representation used at `L01EE/L01F0`. The adapter/island retains the stock output-support calculations that convert that command using REF period, RPM/latency compensation, dwell state, and rolling timing state.

Hardware-facing sequence retained verbatim in behavior:

```text
previous $3FF6 rolling fall count
+ new timing delta
→ $3FE8

$3FE8 result
+ previous $3FDC dwell state
- current dwell interval
→ $3FE6

current dwell interval → $3FDC
new rolling fall count → $3FF6
```

The short `LF3ED` access delays are preserved.

The `$3FEC → $3FE4` mirror/ack at `AC28-AC2E` is retained as an opaque required stock side effect when the EST-monitor/sync tail is included. Its physical meaning does not need to be known.

The spark driver island therefore owns the stock hardware handoff semantics; the custom spark algorithm owns base spark, corrections, knock policy, idle spark, PE/WOT decisions, and other control math.

## Driver-island completion state

| Island | Software command boundary | Status |
|---|---|---|
| Fuel sync | final PW count → `$3FCE` | **LOCKED** |
| Fuel async | final async PW → `$3FF2/$3FFC` trigger | **LOCKED** |
| IAC | desired position → stock step/phase/shadow → `$3062` | **LOCKED** |
| Fuel pump | boolean request → `$FF/$00` at `$306F` | **LOCKED** |
| Spark/EST | final stock-format spark → rolling ASIC handoff | **LOCKED ABI; code port active** |
| MIL | not required for first engine start | **DEFERRED** |
| Other unused I/O | not required for first engine start | **DEFERRED** |

## Safety / integration rule

These islands are not called merely because they exist in the ROM image.

Every active output still requires the clean runtime permission and command-valid gate:

```text
PERM_FUEL + CMD_FUEL_VALID
PERM_SPARK + CMD_SPARK_VALID
PERM_IAC + CMD_IAC_MOTION_VALID
PERM_PUMP + CMD_PUMP_VALID
```

The current engine-off safe runtime never sets the enable token itself. Driver-island code may be present while remaining unreachable from actuator-enable policy.

## Consequence for hardware contract

For the retained first-running-engine scope, physical endpoint polarity/current/topology is no longer an implementation blocker. The software-facing contract is complete once these preserved command islands and the already-mapped read-only input interfaces are used behind the HAL boundary.

Unused I/O is future expansion work, not missing first-start work.
