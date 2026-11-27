# 7060 BAMW and 7427 BMHM bus selections

The stock programs use the same logical address for different purposes. At $4000 BAMW operates an I/O port. BMHM uses the region beginning there for its image. At $3FCE both programs access event hardware, but only BMHM's programmed HC11 selects identify the route. These assignments apply to BAMW $D8 and BMHM $31. They have not been established here for BANF, $85, a D8 port running on a 7427, or a modified image.

## Configuration stores

| Register | BAMW store PC → address = byte | BMHM store PC → address = byte |
|---|---|---|
| INIT | A008 → 103D = 01 | 7108 → 103D = 03 |
| CSSTRH | DB03 → 105C = 00 | CC89 → 305C = 00 |
| CSCTL | DB1D → 105D = 05 | CCA7 → 305D = AC |
| CSGSIZ | DB21 → 105F = 06 | CCAB → 305F = CB |
| CSGADR | DB25 → 105E = 40 | CCAF → 305E = 00 |
| HPRIO | A017 → 103C = 1D | CCA3 → 303C = 15 |

Both request internal-read visibility and program zero stretch. Internal-read visibility can expose data on the bus. It does not create a second address for a byte. Under the F1 definitions, BAMW configures E-clock-valid, active-low GEN and gives PROG priority. BMHM configures address-valid, active-low GEN and I/O selects and gives GEN priority. CPU resources and other higher-priority windows still overlay the nominal ranges. [NXP MC68HC11F1, §§4.4–4.5, Figure 4-4 and Table 4-12](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf)

## Read and write sets

[Filterable instruction ledger](../../maps/structure/7060_7427_select_accesses.csv). Counts below are distinct operand instruction PCs in each select and direction. RMW sites count in both. They measure coverage of the two input inventories, which differ in scope. Instruction fetches, implicit stack operations and external module bodies are outside the ledger.

| Select | 7060 BAMW assigned uses (R / W PCs) | 7427 BMHM assigned uses (R / W PCs) |
|---|---|---|
| CSGEN | $4000–43FF, 1 KiB. Port A read/merge/write, Port B output, Port C input, switched outputs (16 / 20) | Nominal $0000–1FFF, 8 KiB. External working state including $08xx and the optional $18xx module region (229 / 204). Internal RAM and conditional EEPROM take precedence. |
| CSIO1 | Disabled | $3060–37FF. Port and board control (13 / 30). |
| CSIO2 | Disabled | $3800–3FFF. Includes the $3FC0–3FFF event/command interface (35 / 42). |
| CSPROG | $8000–FFFF, 32 KiB program image (461 / 0) | Nominal 64 KiB. Image occupies $4000–FFFF, 48 KiB. $2000–2FFF also decodes to PROG under the assumed map, with backing unknown (1,331 / 0 for PROG). |
| Internal registers | $1000–105F (23 / 42) | $3000–305F after INIT (95 / 96). The $7108 reset write uses the original register page. |
| Internal RAM | $0000–03FF (395 / 251) | $0000–03FF (3,524 / 1,734) |
| Other | Board route unresolved (19 / 25), including the confirmed BAMW injector command at $AA55 → $3FCE–3FCF. All four programmed external select windows exclude that address. | $0E00–0FFF is an internal EEPROM overlay **if** the derivative implements the F1 resource and live CONFIG matches the expected $0B. The $F5D8 write to $0F00 falls here (0 / 1). Indexed sites without resolved byte targets remain separate (175 / 29). |

Neither image's decoded program-select size alone tells us how much ROM was fitted. The **16 KiB difference in image coverage** is specifically $4000–7FFF. BAMW uses parts of that interval for board I/O and out-of-image calls ($5800 family). BMHM places image bytes in that interval. A physical alias would require evidence that two bus addresses select the same storage cell.

## Software shadows, working RAM and next-start state

| Use | BAMW | BMHM |
|---|---|---|
| Mixed Port A byte | $006F ↔ $4000. Read port at EAC4, publish at EACD, update RAM at EAD1. | $004B ↔ $3060. F400 reads inputs, F409 writes mask $90, F40D merges input mask $6F back into RAM. |
| Output image | $0070 → $4002 at EAD5; $0072 → $4007 at EAF1. | $004C → $3062 at F411; $004E → $3067 at F41B. |
| Input image | $4004 → $0071 at EAD8/EADB. | $3064 → $004D at F414/F417. |
| Algorithm workspace | $0052 is a derived coolant lookup index. C1F8–C208 subtracts 16 and clamps it to 0–192 for later coefficient selection. $016B holds previous TPS for transient detection. Both have consumers beyond the instruction that writes them. | $0871–0872 is a working word. $950E saves X selected from idle-state inputs; $9526 adds that word into a saturating calculation. $9C0B also writes it. $0864 is a different lifetime: $9495 stores a delay and $9599 tests it in IAC qualification. Applying the Rev B manual-idle label to stock BMHM would misidentify this byte. |
| Stack scratch | Reset establishes SP at $03FF. | Spark code reads the saved product on the stack at AB9A and AB9E, then replaces the candidate at ABA0. The absolute RAM address depends on SP at entry. |
| Learned fuel trim | $0232–0241, 16 BLM cells. ADCB indexes the table; $01FD holds a selected BLM value. | $02B3–02C7, 21 BLM cells. $F280–F28B seeds them to $80 on recovery. $8E78 and $8E9A read and write indexed cells. |
| Boot retention | The D8 fuel-state evidence identifies the BLM bank as keep-alive state. Its complete power-loss acceptance test was outside this comparison. | $F326 checks ten diagnostic log bytes at $000B–0014; $720C–723E uses the comparison against $0015 to decide recovery, including TPS-zero and BLM reseeding. Independently $723F–726A validates the 52-byte adaptive bank at $02F8–032B and fills it with $80 on rejection. The last byte participates in adaptive accounting. |

The boot paths establish which values firmware expects to reuse. They do not establish how long the board preserves them without power, or prove a RAM/EEPROM alias. The conditional EEPROM window and the learned banks occupy different addresses.

## Evidence and reproducibility

The BMHM ledger joins the repository's factory memory-access inventory to rooted instruction PCs and matching mnemonics, then adds the byte sets and qualifications from the indexed-alias inventory. Unresolved indexed targets are carried as rows. A context-dependent target denotes a possible access on a documented path. Most counts are static. [BMHM direct operands](../../maps/structure/factory_memory_accesses.csv) · [Indexed evidence and conditions](../../maps/structure/factory_global_alias_sites.csv) · [Stock listing](../../source/31/BMHM_HAC_ORG_7100_to_end.asm) · [Boot comparison](../../pseudo-source/reference/boot_retained_contract.md)

The BAMW ledger uses PC-bearing direct symbolic operands in the pinned v0.4 hardware-path extraction plus six traced reset/configuration stores. Word operations include both bytes; direction follows HC11 operand semantics. The source extraction is selective and is not the independent 8,792-instruction stock ROM audit. The 7060 project documents that separate audit and its unresolved indexed operands. [BAMW operand source](https://github.com/snow663/7060HWContract/blob/20294a365857e687933a502c886ecd9dbbb238ea/maps/full/D8_hardware_access_detail_v0.4.csv) · [Stock setup](https://github.com/snow663/7060HWContract/blob/20294a365857e687933a502c886ecd9dbbb238ea/factory-pseudo-source/src/startup/cpu_board_init.c) · [BAMW ROM audit](https://github.com/snow663/7060HWContract/blob/20294a365857e687933a502c886ecd9dbbb238ea/docs/analysis/D8_ROM_VERIFIED_REGISTER_AUDIT_20261106.md) · [BAMW fuel-state evidence](https://github.com/snow663/7060HWContract/blob/20294a365857e687933a502c886ecd9dbbb238ea/docs/algorithms/7060_D8_FUEL_STATE_MODEL.md)
