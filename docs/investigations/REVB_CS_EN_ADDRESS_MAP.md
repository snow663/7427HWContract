# Rev B: CS/EN writes, selected address ranges and software shadows

Image: `0.3.12_engine_only_manual_idle_revB.bin`
SHA-256: `e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`
Trace date: 2026-11-07. CPU addresses equal offsets in the mapped ROM region at `$4000..$FFFF`. Low BIN padding is not live RAM/device contents.

The firmware establishes separate CPU, general-memory and I/O windows. Software output shadows and ALDL address translation are additional, distinct mechanisms. No BIN, XDF or calibration was changed.

The [read companion](REVB_READ_RESOURCES.md) maps operand reads to these
resources, including ADC caller context, board input mirrors, shared words and
the separately qualified boot-checksum footprint. The [read/write audit](REVB_READ_WRITE_AUDIT.md)
adds the admitted RAM-refresh walk and distinguishes the simulator resource
implementation from this conditional F1 interpretation.

## 1. Actual relocation, CS/EN and visibility writes

| Write PC | Instruction bytes | Effective destination | Value | Register / purpose |
|---|---|---|---|---|
| `$7108` | `A7 3D` | `$103D` | `$03` | INIT: RAM page 0, CPU-register page 3 |
| `$CC89` | `A7 5C` | `$305C` | `$00` | CSSTRH: zero programmed stretch fields |
| `$CCA3` | `A7 3C` | `$303C` | `$15` | HPRIO: IRV/internal-read visibility requested on |
| `$CCA7` | `A7 5D` | `$305D` | `$AC` | CSCTL: selects enabled and program/general priority |
| `$CCAB` | `A7 5F` | `$305F` | `$CB` | CSGSIZ: general size/polarity/timing, I/O timing |
| `$CCAF` | `A7 5E` | `$305E` | `$00` | CSGADR: general-select base |

At `$7103`, X becomes `$1000`; `$7106` loads A with `$03`, so `$7108` writes INIT at its reset address. `$710A` then loads X with `$3000`. The call at `$711C` enters `$CC7C` with that X value. This straight-line initializer preserves X; its immediate A loads establish the other values above.

`$AC = 1010 1100`: IO1EN=1, IO1PL=0, IO2EN=1, IO2PL=0, GCSPR=1, PCSEN=1, PSIZ=00.

`$CB = 1100 1011`: IO1AV=1, IO2AV=1, GNPOL=0, GAVLD=1, GSIZE=011. There is no separate GEN-enable bit: its nonzero selected size enables it.

## 2. Range separation

The interpretation below uses the F1-compatible expanded-mode register layout already matched by the repository's hardware contract.

| Resource | CPU address range | Separation |
|---|---|---|
| Internal working RAM | `$0000..$03FF` | Remains at page 0 |
| Internal CPU registers | `$3000..$305F` | Relocated from `$1000..$105F`; not a second mirrored copy |
| General select, CSGEN | `$0000..$1FFF` nominal | 8-KiB selection; internal resources can overlay it |
| I/O select 1, CSIO1 | `$3060..$37FF` | Board I/O writes include `$3060..$306E` |
| I/O select 2, CSIO2 | `$3800..$3FFF` | Includes the used ASIC interval `$3FC0..$3FFF` |
| Program select, CSPROG | `$0000..$FFFF` nominal | Other/internal selections take precedence; this does not mean 64 KiB of fitted ROM |

All four external selections are active-low/address-valid, with zero programmed stretch. GCSPR=1 puts GEN above PROG. The interpretation follows the explicit field definition and Table 4-12; a sentence in §4.5.1 contradicts those priority definitions.

The remainder available to program selection is `$2000..$2FFF` and `$4000..$FFFF`, under the expected internal-resource map. The supplied image's actual code/calibration region occupies the latter. Selection boundaries do not establish which physical chip responds or whether a device ignores address bits.

### What each resource actually means

- **Internal RAM** is the CPU's working storage: variables, saved controller histories, temporary values and the call/interrupt stack. Boot sets SP to `$03FF`, within the 1-KiB interval. This working-memory resource is distinct from an external chip-select window. Low-address padding in a BIN does not supply its runtime contents.
- **CPU registers** control on-chip functions such as timers, ADC, serial communications, ports and address decoding. INIT moves their register block to `$3000..$305F`. After relocation, `$1000..$105F` is in the general external window; it is not a second CPU-register copy.
- **CSGEN** is a general-purpose external selection. It tells attached hardware when a CPU address falls within its configured window. Its nominal 8-KiB span is not a declaration that the board has 8 KiB of RAM there. The `$0800` working-state area and the historical `$1800` interface are within this selection, but sharing a select does not prove they share storage or alias each other. The size encoding `011` selects 8 KiB; `111` disables GEN.
- **CSIO1** selects external board I/O. The firmware uses the small `$3060..$306E` area for board-facing input/output and initialization transactions. The rest of the selected `$3060..$37FF` range is not thereby assigned to known registers or free storage.
- **CSIO2** selects the other external I/O window. The used `$3FC0..$3FFF` ASIC interval contains reference/event observations and fuel/spark/output handoffs in the maintained contracts. That used interval is only 64 bytes inside a 2-KiB selection. Unused addresses do not establish spare RAM, another device, or repeated ASIC aliases.
- **CSPROG** selects external program memory. The image supplies executable code, calibration data, pointer tables and vectors in `$4000..$FFFF`; this address interval is not all executable instructions. The additional `$2000..$2FFF` remainder is a decode consequence, not proof that readable program storage is fitted there. The select configuration alone establishes neither chip capacity nor a flash-programming operation.
- **The conditional EEPROM resource** is on-chip nonvolatile storage under the standard F1 interpretation of the expected CONFIG byte. Its mapping and physical implementation on the actual GM derivative must remain qualified separately from the known runtime comparison.

A chip select identifies a bus destination. A software shadow is a saved value later copied to a destination. IRV makes internal-read data observable externally. These three mechanisms do not create additional independent copies of the same memory by themselves.

### CONFIG adds an important conditional overlay

`$71C6` reads `$303F`; `$71C9` compares it with `$0B`. A mismatch enters the configuration-fault path. This is a runtime check, **not a write of `$0B`**, and the live register response is not contained in the BIN.

With standard F1 EEPROM behavior, an accepted `$0B` implies an internal EEPROM overlay at `$0E00..$0FFF`. Then the external portions of the nominal GEN window are `$0400..$0DFF` and `$1000..$1FFF`. The expected layout must not be confused with measured backing on the GM CPU derivative.

This also bounds the otherwise unexplained `$F5D8` store of `$F7` to `$0F00`: that address lies in the conditional EEPROM interval. Its intended effect and the derivative's implemented memory still need evidence; a lone store does not identify an external device.

### Non-overlapping map under that expected layout

Every address occurs once in the table below. It assumes the standard F1 internal resources and a live CONFIG value matching the firmware's expected `$0B`; it is not a measured physical-board memory inventory.

| CPU range | Bytes | Selected resource / interpretation |
|---|---:|---|
| `$0000..$03FF` | 1,024 | Internal RAM |
| `$0400..$0DFF` | 2,560 | External GEN selection; backing not identified |
| `$0E00..$0FFF` | 512 | Conditional internal EEPROM overlay |
| `$1000..$1FFF` | 4,096 | External GEN selection; former reset-register addresses no longer select the CPU registers |
| `$2000..$2FFF` | 4,096 | Remaining program selection; backing not established |
| `$3000..$305F` | 96 | Internal CPU registers |
| `$3060..$37FF` | 1,952 | External IO1 selection |
| `$3800..$3FFF` | 2,048 | External IO2 selection |
| `$4000..$FFFF` | 49,152 | Remaining program selection; supplied code/calibration/vector image |

The two external GEN portions total 6,656 bytes in this expected layout, not an additional 8 KiB alongside internal RAM/EEPROM. The overlapping nominal-selection table and this resource partition answer different questions.

## 3. What is visible on the external bus

The `$15` write to HPRIO sets IRV. Under the F1 layout this exposes internal-read data on the external data bus. It does not copy RAM into another CPU address range. Mode bits in HPRIO have normal-mode write restrictions; the literal `$15` store is not proof that expanded mode was changed to single-chip mode.

## 4. Actual software output shadows

The common publication path is `$F3EE..$F41F`:

| RAM source | Hardware destination | Exact operation |
|---|---|---|
| `$004B`, mask `$90` | `$3060`, output bits `$90` | `$F405/$F407/$F409`; input bits `$6F` sampled earlier are merged back into RAM at `$F40C/$F40D` |
| `$004C` | `$3062` | `$F40F/$F411`: full-byte copy; retained IAC phase/enable fields share this shadow |
| `$004E` | `$3067` | `$F419/$F41B`: full-byte copy |
| `$3064` hardware input | `$004D` RAM | `$F414/$F417`: reverse-direction input mirror |
| `$0072.7` | `$3FFD.3`, inside word `$3FFC` | Inverted bit update through the word read/modify/write at `$F3EF..$F3FD` |

The last path samples the shared hardware word, sets low-byte bit 3 if RAM bit 7 is clear, and clears it if RAM bit 7 is set. It preserves other sampled bits. This is not a whole-word RAM mirror.

The nearby boot stores `$3061=$90`, `$3063=$FF`, `$3065=$00` and word `$306E=$7FFF` configure board-facing state within IO1. They are separate from the CPU chip-select registers. Their electrical direction/enable identities are not established merely by the write pattern.

## 5. ALDL can create apparent aliases

At `$F8B8..$F8CA`, the reply producer treats encoded `$1000..$3FFF` as word-source addresses. Unless `$0050.3` is set, `$F8C7` executes `ANDA #$CF` on the address high byte: CPU address = encoded address AND `$CFFF`. The code then reads the resulting address. Outside that interval it takes the ordinary byte-source path.

| Encoded request | Normal CPU address actually read | With `$0050.3` set |
|---|---|---|
| `$1000` | `$0000` | `$1000` |
| `$1800` | `$0800` | `$1800` |
| `$3000` | `$0000` | `$3000` |
| `$3060` | `$0060` | `$3060` |
| `$3FC0` | `$0FC0` | `$3FC0` |
| `$4000` | `$4000`, byte-source path | Same |

This is reply-address arithmetic. It does not establish physical mirrors between `$0800/$1800`, `$0060/$3060`, or any other pair. A literal CPU instruction accessing `$1800` still accesses `$1800`.

## 6. Trace coverage and evidence

The exact-image rooted sweep contains 6,449 instruction starts. A conservative normal-return analysis covered 132 procedure entries, including dispatcher/vector roots. Its finite destination effects identify the six configuration/visibility sites listed above and no additional finite-resolved remap site. The initializer's recovered callers all provide X=`$3000`.

There are 101 indexed write instruction sites in the abstract contexts. Seventeen have at least one unknown-address context; twenty-two have a formal entry-register context. Those categories are qualifications, not additional proven CS writes or a claim of complete wildcard-address exclusion. Hardware aliases, interrupts, invalid pointer/stack histories and arbitrary external behavior remain outside that closure.

Bounded actual-instruction witnesses checked the INIT store, CPU setup values, 34 normal/factory-flag ALDL address cases and the main software-shadow publication. The fixture records memory transactions; it does not simulate physical chip-select pins, INIT relocation, EEPROM or peripheral electrical behavior.

The [evidence directory](../../maps/maintenance/revb_cs_decode/README.md) separates writes, nominal/conditional windows, the expected non-overlapping map, software shadows and ALDL translations. JSON files preserve exact byte excerpts, abstract contexts and execution results. The four reference workbooks, firmware and definitions remain unchanged: this adds resource/decode context to the existing register roles, not new memory allocation or a remap.

From the repository root:

```sh
# Replay committed local instruction excerpts; no full BIN required.
python tools/verify_revb_cs_decode.py --check-recorded

# Re-extract setup operands and tables from the exact supplied Rev B.
python tools/trace_revb_cs_decode.py --rom /path/to/revb.bin --output-dir /tmp/cs-decode

# Recompute the full-image abstract indexed-write scan.
python tools/trace_revb_cs_indexed.py --rom /path/to/revb.bin --output /tmp/cs-indexed.json

# Execute the bounded witnesses against the exact full image and compare results.
python tools/verify_revb_cs_decode.py --rom /path/to/revb.bin
```

The recorded verifier replays setup/ALDL/shadow witnesses and checks their correspondence with extracted stores and map tables. It does not reproduce the 132-procedure whole-image abstract scan from partial excerpts; that requires `--rom`. Static relationships and controlled instruction execution do not measure selection pins or resolve physical aliases.

Hardware reference: [NXP MC68HC11F1 Technical Data](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf), §§4.2, 4.3.2.1–2, 4.5 and Table 4-12; HPRIO/IRV in §4.3.1.1. Firmware bytes and these manual-derived interpretations are separate evidence.
