# Factory engine calculations: upstream documentation closure

The previously open upstream fuel/spark calculation work is documented against actual stock BMHM bytes. This closes the named air-model, VE, commanded-AFR/PE/startup, AE, O2/BLM, and spark-modifier dependencies of the completed running-fuel and spark handoff contracts. The equations describe the resident software, including its exceptional branches and retained state. This is not a declaration that every factory engine controller, diagnostic, transmission routine, or physical output is understood.

## Completed calculation chain

| Calculation | Documented result and state | Contract |
|---|---|---|
| MAP/BARO/TPS/coolant normalization and RPM coordinates | `$01C6/$01C0/$01C9/$01CF/$01CC/$01D9/$0006/$0283`, period and RPM filters; boot and alternate RPM path | [Upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) |
| Density, charge temperature and VE | `$0257/$0236/$0231`; exact offsets, different VE/spark axes, MAT blend and rounding | [Upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) |
| Startup, open-loop/idle AFR and PE | `$02C8/$02C9/$02CB`, `$024A/$024B/$0278`; qualification, delays, slew, decay, caps and overrides | [Upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) |
| MAP/TPS AE and histories | `$023E/$023F/$023C/$023D`, `$01DC/$01DE/$01C7`; threshold hysteresis, gains and update admission | [Upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) |
| Crank equation and reference-event routing | `$02CF/$02CD/$02CE`; main-task versus REF delivery, event gain, async and alternate timer route | [Upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) |
| EGR inputs to engine arithmetic | `$01AE/$01B2/$006E bit7`; desired lookup, fraction calculation and filter | [Upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) |
| Closed-loop admission, O2 I/P and BLM | `$003E`, `$020F/$027A/$026F`, cell selection/learning/reset at `$02B3-$02C7` | [Closed loop and learning](FACTORY_CLOSED_LOOP_AND_LEARNING.md) |
| Composite spark and modifiers | Word `$01FD`; base, coolant, BARO, EGR, MAT, PE/startup, idle, transient and decel | [Upstream spark](FACTORY_UPSTREAM_SPARK_CALCULATIONS.md) |
| Knock producers and final command | Knock ISR, decay/fault, low-octane learning, burst, normal KR, signed limits and service edits through `$AB3E` | [Upstream spark](FACTORY_UPSTREAM_SPARK_CALCULATIONS.md) |
| Running fuel through device command | Air mass/divisors, corrections, cut/decel, packet accounting, shaping and sync/async writes | [Fuel integer handoff](FACTORY_FUEL_INTEGER_HANDOFF.md) |
| Normal spark through device command | Period/adaptive terms, startup gain, stack bridge and four ordered writes | [Spark integer handoff](FACTORY_SPARK_INTEGER_HANDOFF.md) |

These rows can be crossed off the upstream-calculation worklist. Their explicit interfaces below remain relevant when using the equations; they are not newly completed controller dossiers.

## Byte authority and audit artifacts

Authority is the 65,536-byte stock image, SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`. Both supplied BMHM filenames match it. CPU `$4000-$FFFF` uses the same full-file offsets. File `$0000-$3FFF` is padding, while CPU `$0000-$3FFF` includes RAM and hardware. No low-memory execution is inferred from that padding.

The original HAC remains unchanged. For this scope, actual bytes and decoded operands take precedence over inherited comments. Truck `2.bin` is a separate, previously recorded calibration authority; these new equations and stock table bytes do not reverify that tune.

| Artifact under `maps/structure/` | What it establishes |
|---|---|
| `bmhm_upstream_rom_evidence.json` | Full-image identity, source hash, reviewed instruction excerpts, stock calibration `$4000-$70FF`, coolant conversion bytes `$FC45-$FE44`, and pointer-data evidence |
| `factory_upstream_blocks.csv` | 50 reviewed blocks, exclusive ends, outputs, local execution contexts and documentation links |
| `factory_upstream_instructions.csv` | 3,403 instruction starts, bytes, addressing modes and explicit memory references |
| `factory_upstream_branches.csv` | 826 local branch rows, exact condition, target and fallthrough |
| `factory_upstream_state_contracts.csv` | 54 selected handoff/working states, width, reviewed direct stores, other listing candidates and initialization class |
| `factory_upstream_external_interfaces.csv` | The three low-memory calls encountered in these blocks; guards/effects retained as interfaces |

The source index's apparent `$B968 STAB $0062` is not an additional RPM producer in the reviewed flow. Bytes `$B967-$B96C` are words `$62D7,$62D7,$651F`, selected as lookup pointers at `$B5A0-$B5A9`. The table reader and these bytes are captured; the state audit explicitly classifies the candidate. This local classification does not assert that every data-as-code row in the whole listing has been corrected, or prove global absence of an alternate entry.

The verifier checks ROM identity, decoding boundaries, branch/state inventories, regeneration consistency and document presence. It does not mechanically prove every explanatory equation or emulate complete operating scenarios. The equations were reduced from the instructions; the existing downstream replay evidence retains its separate scope.

## Shared integer and lookup rules

Unless stated otherwise, byte/word reads are unsigned, words are big endian, and arithmetic wraps only where explicitly written. `hi(w)` is the high byte; `u8/u16` wrap modulo 256/65536; `sat8/sat16` clamp a nonnegative value at 255/65535. `C[a]` and `W[a]` distinguish ROM bytes and words; RAM widths are stated at each use.

| Operation | Exact rule |
|---|---|
| Rounded byte product | `R8(a,b) = floor((a*b+128)/256)` |
| `$F550` byte-times-word | `M(a,w) = floor((a*w+128)/256)` |
| Doubled product, truncated | `K2(a,b) = hi(sat16(2*a*b))` |
| Doubled product, rounded | `K2R(a,b) = hi(sat16(2*(a*b+64)))` |
| Fractional divide quotient | `Q(n,d)=floor(65536*n/d)` when `d>n`; otherwise `$FFFF` (including zero divisor) |
| `$F459` byte-target filter | `lag8(a,old,k)=old+floor((((a<<8)-old)*k+128)/256)` |
| `$F436/$F479` word-target filter | `lag16(t,old,k)=old+floor(((t-old)*k+128)/256)` |

Filter differences are mathematical signed differences, and floor is toward negative infinity. These formulas preserve the asymmetric integer rounding on falling signals. `$F436` takes old word X and gain at `[Y]`, preserving X. `$F479` takes the old word at `[X]` and gain `[Y]`; it writes a partial intermediate through X before returning the final D, which the caller then stores. `$F459` takes old word X and gain B, preserving X/Y. That intermediate write is not an additional final filter state.

For a knot pair `lo,hi`, interpolation uses `r=R8(abs(hi-lo),fraction)` and returns `lo+r` on a rising slope or `lo-r` on a falling slope. It is not one floating-point weighted average rounded at the end.

| Entry | Header/input behavior |
|---|---|
| `$F4C1` (`L1`) | X points at first knot; index `A>>4`, fraction `(A&15)<<4` |
| `$F4BD` | First `A=max(A-B,0)`, then `$F4C1` |
| `$F499/$F49A` (`H1`) | Clamp A to byte `[X]`, increment X, then subtract the supplied lower offset B (`$F499` supplies B=0), then `$F4C1` |
| `$F4B6` (`S1`) | Header `[X]` is a multiplier; high/low bytes of `A*[X]` are knot index/fraction; first knot X+1 |
| `$F4A4` | Subtract lower header byte with zero floor, cap to next header byte, use third header byte as index multiplier; first knot X+3 |
| `$F4DE` (`L2`) | Header offsets for A then B, each subtracted with zero floor; third byte is row stride. First data X+3. Two rounded column interpolations, then rounded row interpolation |

`L2(A,B,header)` uses A for rows and B for columns. It has no general upper-axis clamp: the caller's transforms and adjacent reads matter, including zero-weight neighbor reads. A mode byte before a header is not part of the header.

The ISA [NXP M68HC11 reference guide](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf) distinguishes an **all-selected-bits** `BRSET` from any-bit testing. `BRCLR` requires all selected bits clear. `BIT/AND` followed by a nonzero branch commonly means any bit. `BMI/BPL` tests N alone; `BLT/BGT` uses N xor V. The documents preserve that distinction, carry/borrow and byte wrap rather than substituting general signed comparisons. The upstream evidence was decoded with those rules; multi-bit conditions do not depend on the older CPU model's BRSET implementation.

## Update admission and state age

TOC3's nominal tick is 6.248474 ms and the phase byte cycles `$00-$9F`. These are opportunities to execute; busy/pending coalescing and mode gates can change wall time. A table result and the state consuming it need not be from the same tick.

| Producer | Local admission | Nominal ticks |
|---|---|---|
| MAP lag `$7BA7` | Ordinary common fast group | 1 |
| Load/RPM/spark `$A466`; fuel `$7D4B` | Ordinary even / odd groups | 2 each |
| TPS AE-history lag `$7F73` | Odd group, phase bit1 set | 4 |
| O2 I/P `$863D` | Fuel tail, phase bit1 clear | 4 |
| Battery state `$8613` | Fuel tail, phase bit1 set | 4 |
| AFR/PE/BLM `$891E` | Fuel tail, low three phase bits =7 | 8 |
| EGR fraction `$D03E` | Ordinary phase low two bits =0 | 4 |
| BARO `$C583`, spark gains `$CA6B`, EGR demand `$CF16` | Slots 1, 7, 9 | 16 |
| CTS/environment `$C96A/$C9F7` | Slot4, phase bit4 clear | 32 |
| Charge denominator/offset `$E2C8-$E303` | Slot F | 16 |
| AE gains/startup/closed-loop admission `$E30B-$E561` | Slot F, phase bit4 clear; `$E306` returns on the other half | 32 |
| Normal KR decay `$CEBB` | Slot8, phase bit4 clear | 32 |
| Low-octane learning | Slot6, full phase `$06` only | 160 |
| Startup spark hold `$02CC` decrement | Slot F, full phase `$0F` only | 160 |
| PE `$0269`, PE-exit `$0276`, warm-idle `$0271` timer steps | Full phases `$07`, `$17`, `$27` respectively | 160 |
| PE vehicle-change sample `$0818` | Full phase `$9F` | 160 |
| Crank/event counts and additional-AFR decay | REF interrupt; conditional on event/mode | Event driven |

The boot calls additionally populate some states before periodic execution. REF IRQ and knock IRQ can interleave with scheduler work; documented atomic sections only protect their specific operations.

## Initialization and interfaces

Boot clears `$0036-$00FF`, `$0100-$029C` and `$0800-$08FF` unconditionally through the reviewed indexed-clear helpers. `$0000-$0035` and `$029D-$034D` are conditionally cleared as retained/NV working storage. Thus IAC position/mode bytes and BLM cells `$02B3-$02C7`/startup bytes `$02C8-$02CF` do not inherit the unconditional clears. Their seeds/reset rules are described in the producer contracts. Byte seeds at `$7396-$73FC` do not magically initialize both bytes of a word; prior clear/retained-memory rules still apply. Boot seeds AFR from `$48E7` and selected BLM to128, then clamps the cells.

| Interface | What is closed here | Separate owner or missing implementation |
|---|---|---|
| Raw ADC inputs, battery `$0055/$00A7`, MAT `$022F/$0230`, VSS `$0284`, runtime word `$00FD`, engine/gear/diagnostic flags | Exact read sites, coordinate conversions and consuming branch rules | Resident diagnostic and switch/gear owners now documented in [DTE closure](FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md); electrical scaling/acquisition timing remain separate |
| IAC target `$0857`, ratio `$006C`, IAC effort `$0858` | Consumers plus the now-completed [IAC/RPM/VSS producer and output-service contracts](FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md) | Physical pins/motor response; resident switch/gear/diagnostic owners now linked through the DTE closure |
| Transmission retard `$015A` and `$00A4` | Spark subtraction and limit selection | Now documented through `$C40A/$DA6F/$DAE2` in [transmission control](FACTORY_TRANSMISSION_CONTROL.md); physical scaling and interrupt/device behavior remain separate |
| Governor inputs / optional `$90D3` call, fuel's governor/cut inputs | Now-completed [governor target/actuator, speed production and limit contract](FACTORY_RPM_VSS_GOVERNOR.md) | Resident TCC output owners now documented in the transmission contract; physical actuator, factory-test and opaque1809 remain separate |
| `$0086 bit6` extensions | AFR `$8C6A→$1800`, spark `$A9E4→$1812`, EGR `$D029→$1815`: guards, ordering and subsequent local overrides | Low-memory implementation absent from the mapped stock image; no effect is invented. Existing spark handoff's `$180F` is likewise separate |
| Service command payloads | Actual local AFR/spark/EGR override bits and values | Full receive/command/authorship state machines |
| Device-facing outputs | Documented software write order and values | ASIC interpretation, injector/ignition physical response and complete interrupt/timing behavior |

All listed resident branches are documented, including optional calibration branches. Enabling an opaque extension changes the scope: the normal resident calculation cannot predict unknown extension mutations without that implementation. Physical-unit normalization is retained only where separately established; raw integer closure does not require guessing sensor or hardware units.

## Reproduce

```bash
python tools/verify_factory_upstream.py --rom /path/to/BMHM.BIN
python tools/verify_factory_upstream.py --check-recorded
```

Full-image mode checks the image SHA before rebuilding the inventories. Recorded mode checks committed excerpts and generated-file consistency without claiming a fresh independent ROM read. IAC/output service and RPM/VSS/governor software are now completed in the linked companion closure. The resident transmission/emissions/diagnostic and peripheral-speed owners are now documented in [DTE closure](FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md). The queue continues with full serial/service/factory-test machines, opaque extensions and whole-program reachability/ownership. Physical interfaces retain their separate evidence level. No whole-ROM completion percentage is derived from these bounded closures.
