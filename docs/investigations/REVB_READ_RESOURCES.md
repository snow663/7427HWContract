# Rev B: reads by resource, address range and purpose

This is the read companion to the [CS/EN, resource and shadow map](REVB_CS_EN_ADDRESS_MAP.md).
It traces the exact `0.3.12_engine_only_manual_idle_revB.bin`, SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
The BIN, XDF and calibration are unchanged. TS00 truck testing and fine-tuning
remain the active checkpoint.
The [subsequent read/write audit](REVB_READ_WRITE_AUDIT.md) corrects the shared
shadow labels, adds the qualified RAM-refresh footprint and documents timeout,
discarded-load and simulator-resource findings. The ordinary finite counts
below remain separate from that admitted refresh walk.

The extraction finds **2,221 explicit operand-read sites** in the 6,449 rooted
instructions: 1,927 fixed-address sites and 294 indexed sites. Of these, 425
are read/modify/write instructions. A site is an instruction address, not an
execution count, distinct sensor or independently proved live operating path.
Each site links to its functional group from the whole-image reader.

## Resource map and read coverage

These are CPU addresses. The resource interpretation is conditional on the
standard F1 layout and live CONFIG value `$0B` that boot expects. The BIN
contains the comparison, not a measurement of that value or proof of the GM
derivative's physical resource implementation. Chip-select windows identify
selections; they do not establish installed memory capacity or physical aliases.

| CPU range | Expected resource | Fixed read sites | Indexed sites with a finite target here | Distinct finite operand bytes | Function of the identified reads |
|---|---|---:|---:|---:|---|
| `$0000–$03FF` | Internal RAM | 1,422 | 37 | 382 | Published sensor values, engine state, flags, histories, calculation scratch and pointers. |
| `$0400–$0DFF` | External GEN selection; backing unconfirmed | 87 | 2 | 55 | Identified reads are engine working state around `$0800`; the selection does not prove RAM fills the whole window. |
| `$0E00–$0FFF` | Conditional internal EEPROM overlay | 0 | 0 | 0 | No fixed or finite indexed operand identified here. EEPROM presence/enable remains conditional. |
| `$1000–$1FFF` | External GEN selection; backing unconfirmed | 0 | 0 | 0 | No fixed or finite indexed operand identified here. |
| `$2000–$2FFF` | Program selection; backing unconfirmed | 0 | 0 | 0 | No fixed or finite indexed operand identified here. |
| `$3000–$305F` | Internal CPU registers | 15 | 59 | 26 | Timer timestamps/control, ADC status/results, serial status/data and CONFIG qualification. |
| `$3060–$37FF` | External IO1 selection | 3 | 3 | 4 | Board control/strobes, input sampling and bit-preserving updates. |
| `$3800–$3FFF` | External IO2 selection | 28 | 0 | 16 | Shared timing/status words used by reference, spark and knock-related paths. |
| `$4000–$FFFF` | Supplied program/calibration/vector region | 372 | 111 | 523 | Calibration operands, lookup headers/data, dispatch/descriptive pointers and ROM data. Boot checksum has a separate qualified footprint below. |

Counts can overlap when a site's finite target set crosses resources. A word
operand covers both bytes. Zero means no identified fixed/finite operand in
this analysis, **not** proof that a range is unreadable, unused or unreachable
through a runtime-selected pointer. The BIN's padding below `$4000` is not a
snapshot of runtime RAM, registers or external hardware.

## Working-state reads: RAM and the GEN-selected state area

Sensor processing generally reads a published RAM value after hardware
sampling. It then filters, scales or compares that value and stores the result
for downstream consumers. Other reads recover previous commands, counters,
mode bits and learned/history values. Reading RAM therefore need not mean
sampling a physical input at that instant.

For example, raw TPS is published at `$00A6`; the normalized engine-TPS
producer publishes `$01D9`. The custom IAC-change enrichment gate reads
`$01D9`, not an ADC register. Its air-command difference reads current and
previous controller state. These are distinct stages, even though they
ultimately participate in the same engine response.

The [per-byte inventory](../../maps/maintenance/revb_reads/READ_ADDRESSES.csv)
lists finite consumers and finite writer sites. A writer list is a may-write
cross-reference: it does not prove which writer ran last, interrupt ordering,
initialization of every read or complete ownership. Wider runtime pointer
contexts remain in the separate context file.

## CPU-register reads

The following table groups all 34 identified hardware operand forms, including
the IO1/IO2 forms described later. Exact PCs, widths, R versus RW access and
functional-group names are in [HARDWARE_READS.csv](../../maps/maintenance/revb_reads/HARDWARE_READS.csv).

| CPU-register operand | Firmware purpose |
|---|---|
| `$3000` PORTA; `$3008` PORTD | Read pin/port state; PORTD also participates in bit-preserving control updates and sensor-multiplexer selection. |
| `$300B` CFORC | Read operand of two output-compare force-control RMW instructions at `$75CE` and `$7601`. This is a control update, not a sensor sample. |
| `$300E–$300F` TCNT | Read the free-running timer word for timing calculations and scheduling. |
| `$3012–$3013` TIC2 | Read the captured timer word in the retained input-capture path. |
| `$301A–$301B` TOC3; `$301C–$301D` TOC4; `$301E–$301F` TOC5 | Read scheduled compare timestamps for dispatcher and fuel-output timing. These are programmed timing state, not necessarily observed output edges. |
| `$3020` TCTL1; `$3022` TMSK1 | RMW operands for timer action and interrupt-enable updates. |
| `$3023` TFLG1 | Read timer status for event/service decisions. |
| `$302D` SCCR2 | Read serial-control state. |
| `$302E` SCSR; word `$302E–$302F`; `$302F` SCDR | Read serial status and receive data. A word read starting at SCSR also consumes the adjacent data byte. |
| `$3030` ADCTL | Test ADC sequence-completion status. |
| `$3031`, `$3032`, `$3033`, `$3034` ADR1–ADR4 | Read a result slot; sensor meaning depends on conversion sequence and external multiplexer state. |
| `$3038` OPT2 | RMW operand for operating-option control. |
| `$303F` CONFIG | Boot reads at `$71C6`, compares `$0B` at `$71C9` and selects the qualified or alternate path. Expected value is not proof of the live value. |

An ISA RMW read exists even when its purpose is preserving bits for a write.
That alone does not establish meaningful hardware readback for every control
register. Peripheral-specific write-only behavior, read-clear rules, ADC
completion, word latching and pin behavior are not certified by the controlled
byte-storage witnesses.

No fixed or finite indexed reads of CS registers `$305C–$305F`, relocated INIT
`$303D` or HPRIO `$303C` were identified. Their setup writes are documented in
the CS/EN companion. This is not an exclusion of every runtime-selected read.

### ADC result slots acquire meaning from their caller

| Read PC | Result address | Published destination or use | Traced context |
|---|---|---|---|
| `$F24C` | `$3031` ADR1 | `$00A6` raw TPS | Fast sensor sampling. |
| `$7528` | `$3031` ADR1 | `$082E` raw MAP | Separate reference-event conversion path. |
| `$F254` | `$3032` ADR2 | `$082E` raw MAP | Fast sensor sampling; the wrapper can skip this publication through `$0050.0`. |
| `$F259` | `$3033` ADR3 | `$01D5` raw O2 | Fast sensor sampling. |
| `$F21A` | `$3034` ADR4 | `$082D` raw coolant | Coolant sampling path. |
| `$F23F` | `$3034` ADR4 | `$00A7` battery sample | Spark/idle battery path. |
| `$C57D` | `$3034` ADR4 | `$0055` battery sample | Reference-event battery path. |
| `$F236` | `$3032` ADR2 | `$082F` auxiliary sample | Retained sampling; physical signal identity unresolved and the former consumer is removed. |
| `$DC0A` | `$3034` ADR4 | Complement then `$0230` raw MAT | Inverted MAT sample before downstream processing. |
| `$CEF1` | `$3034` ADR4 | Knock-related diagnostic processing | Context-specific sample; this does not make ADR4 a permanent knock-energy register. |

Keep the hardware slot name separate from the raw RAM publication and the
processed engineering value. A result address alone cannot justify labeling
every read as TPS, MAP, battery or temperature, nor establish its scaling.

## Board I/O reads and software shadows

| Operand | What the code obtains or preserves | Scope |
|---|---|---|
| `$3060` byte | Board control/status state, including a read used for a bit-preserving update. | Exact physical decode remains qualified. |
| `$3062` byte | Existing byte during two reference-strobe RMW updates. | The read supports a control write; it is not an independently identified input sample. |
| `$3064` byte | Sampled board digital inputs, copied to RAM `$004D`. | This is a hardware-to-RAM software mirror; individual physical input identities require confirmation. |
| `$3066` byte | Existing board byte read by `$F3E4` during a bit-update sequence. | Read and later store are separate instructions. Physical function remains unresolved. |

The output-shadow flush reads RAM `$004B`, `$004C` and `$004E` to issue board
writes at `$3060`, `$3062` and `$3067`. Those RAM reads are not hardware
readback. Conversely, `$3064 → $004D` actually samples hardware and publishes
an input mirror. Neither direction is a physical address alias or CPU resource
relocation. The CS/EN guide contains the masks and exact write sequence.

## IO2 shared-word reads

| Word start | Bytes consumed | Established software role |
|---|---|---|
| `$3FC0` | `$3FC0–$3FC1` | Reference-pulse period sample used in engine timing calculations. |
| `$3FC8` | `$3FC8–$3FC9` | Knock-observation counter sample. |
| `$3FCA` | `$3FCA–$3FCB` | Event/EST feedback counter sample. |
| `$3FDC` | `$3FDC–$3FDD` | Spark dwell/period scheduling state. |
| `$3FEC` | `$3FEC–$3FED` | EST-related status word. |
| `$3FF6` | `$3FF6–$3FF7` | Rolling EST-related state word. |
| `$3FFA` | `$3FFA–$3FFB` | Packed shared status word. |
| `$3FFC` | `$3FFC–$3FFD` | Shared latch/status word read by several paths and bit updates. |

These are the firmware's observed uses and operand widths. They do not define
every bit's electrical meaning, an undocumented ASIC's full register map or
hardware word-read side effects. The omitted VSS role at `$3FC4` stays preserved
in the maintained register; no rooted read is invented for it.

## ROM data, runtime-selected reads and the checksum

ROM reads include thresholds, curve/table headers and entries, dispatch data,
and descriptors that supply further pointers. For example, `$F888` executes
`LDX 9,X`: with the documented descriptor binding it consumes the word at
`$5216–$5217` and obtains a source pointer. This is distinct from the RAM
commanded-AFR value at `$024A`; a descriptor read is not a write to that value.

For indexed sites, 208 have at least one finite abstract context and 110 have
at least one nonfinite context. **24 occur in both counts**: 184 are finite-only,
24 mixed and 86 nonfinite-only. Generic function-entry parameters, calls,
widening and branch feasibility remain qualified. A formal generic context is
not proof that a real caller can choose every address. Conversely, finite
contexts do not erase unresolved contexts at the same instruction.

The addressed ALDL reply path is an actual runtime-selected word read, not a
new hardware mirror. In normal mode, selected source addresses in
`$1000–$3FFF` are ANDed with `$CFFF` before the load; `$0050.3` bypasses this
translation. Thus a normal request for `$3060` reads `$0060`, while the bypass
case reads `$3060`. A normal `$1800` request reads `$0800`. The read witnesses
exercise both address-selection modes. They do not prove what every selected
physical address returns or model peripheral read side effects.

Boot loads `X = $4008` at `$71D2` and calls `$F2AA` at `$71D5`, after the CONFIG
qualification. The aligned loop reads **all 49,144 bytes `$4008–$FFFF`** as data:

| Read PC | First byte | Last byte | Stride | Reads in this boot call |
|---|---|---|---:|---:|
| `$F2C7` | `$4008` | `$FFF8` | 8 | 6,143 |
| `$F2CB` | `$4009` | `$FFF9` | 8 | 6,143 |
| `$F2CF` | `$400A` | `$FFFA` | 8 | 6,143 |
| `$F2D3` | `$400B` | `$FFFB` | 8 | 6,143 |
| `$F2D7` | `$400C` | `$FFFC` | 8 | 6,143 |
| `$F2DB` | `$400D` | `$FFFD` | 8 | 6,143 |
| `$F2DF` | `$400E` | `$FFFE` | 8 | 6,143 |
| `$F2E3` | `$400F` | `$FFFF` | 8 | 6,143 |

This footprint is qualified to that boot caller; arbitrary helper entry is
separate. The remainder loop at `$F2B9` is not executed for this aligned start.
The checksum reaches code, calibration and vectors alike, so it cannot be used
to claim every covered byte is a tuning parameter or control-routine input.
It is reported separately from finite abstract footprints, which overlap it.

## Fetches and implicit stack reads

The explicit operand inventory excludes instruction fetching. The rooted sweep
covers 15,272 instruction bytes; the fetch-range file records their union, not
runtime frequency or a cycle-accurate bus trace. Some instructions read their
own code region as checksum data, so fetch and operand categories overlap.

There are also 187 implicit stack-read sites: PULA/PULB consume one byte,
PULX/PULY and RTS consume two, and RTI restores the nine-byte HC11 interrupt
frame. Their addresses depend on the current stack pointer. They are not
assigned fixed RAM ownership just because boot initializes the stack.

The 21 vector-word candidates at `$FFD6–$FFFF` are recorded separately.
Reset/interrupt admission and operating mode determine which vector is fetched;
the table does not claim every vector is exercised in operation. These three
categories cannot simply be added to operand coverage as disjoint memory.

## Evidence, verification and maintained reference

The [extraction directory](../../maps/maintenance/revb_reads/README.md) provides
all read sites, indexed contexts, finite byte consumers/writers, hardware
operands, resource totals, checksum strides, stack reads, fetch ranges and
vector candidates. It also contains exact local instruction excerpts and 22
bounded CPU read witnesses. Those witnesses check CONFIG branches, ADC status,
sample publications, serial status/data ordering, board mirrors, shared/period
words, ALDL address selection, ROM descriptors/lookups, the checksum address
walk and RTI frame restoration.

The initial read extraction added `$300B` and `$3066`; their original
roles were already recorded in the write reference. That update preserved prior address/role/use
values and the other two tabs. The hardware read tab has 44 entries. The later
read/write audit updates both maintained books separately; both OEM books stay
unchanged.
[REGISTER_UPDATES.json](../../maps/maintenance/revb_reads/REGISTER_UPDATES.json)
records the before/after workbook identities and supporting PCs outside the
clean address/role columns.

```sh
# Fresh full-image extraction and comparison; rejects any other BIN hash.
python tools/trace_revb_reads.py --rom /path/to/revb.bin

# Intentionally update recorded extraction after reviewing changes.
python tools/trace_revb_reads.py --rom /path/to/revb.bin --record

# CI/local replay without distributing the full BIN.
python tools/trace_revb_reads.py --check-recorded
python tools/verify_revb_cs_decode.py --check-recorded
python -m unittest discover -s tests -p 'test_revb_*.py' -v
```

Recorded verification decodes the committed read instructions, checks context,
byte/resource/table consistency and replays the scoped witnesses. It does not
regenerate the 132-entry abstract analysis from incomplete image excerpts.
The checksum witness verifies the actual address walk and sum of the supplied
fixture; recorded replay contains only selected excerpts and synthetic remaining
bytes. **Only full-image mode additionally verifies the released checksum word
against all released ROM data.** Neither mode models physical chip selects,
EEPROM behavior, ADC completion, peripheral read side effects, aliases or
interrupt histories. Use the exact full BIN for fresh whole-image analysis.
