# Rev B resource-decode evidence

Read the [resource and address-range guide](../../../docs/investigations/REVB_CS_EN_ADDRESS_MAP.md)
for the purpose of RAM, CPU registers, general/program memory selects, I/O
windows, the conditional EEPROM overlay, IRV, board shadows and ALDL mapping.

All records identify the exact released Rev B image, SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
No full BIN is included here.

| File | Content and evidence scope |
|---|---|
| `CS_EN_WRITES.csv` | Exact INIT, CS and HPRIO write PCs, bytes, destinations, values and caller context. |
| `ADDRESS_WINDOWS.csv` | Overlapping nominal selections and separately qualified internal/remaining windows. These rows are not a disjoint physical-device inventory. |
| `EFFECTIVE_EXPECTED_MAP.csv` | Non-overlapping 64-KiB partition under standard F1 resources and the runtime CONFIG value the firmware expects. The live value and GM derivative's implementation are not read from the BIN. |
| `SOFTWARE_SHADOWS.csv` | The main RAM-to-board shadow flush and reverse input mirror, separate from CPU relocation. |
| `ALDL_ADDRESS_MAPPING.csv` | Normal versus `$0050.3`-qualified reply source addresses. This is software arithmetic, not a physical alias map. |
| `EVIDENCE.json` | Image identity, exact local byte excerpts, setup stores and the CONFIG comparison. |
| `INDEXED_SCAN.json` | Recorded 132-entry normal-return abstract scan, finite CS/visibility write sites, initializer bindings and qualified indexed-write contexts. |
| `EXECUTION_WITNESSES.json` | Controlled-memory instruction results: boot/setup, 34 ALDL-address cases, main shadow publication and two shared-word bit cases. |

## Check or regenerate

```sh
python tools/verify_revb_cs_decode.py --check-recorded
python tools/trace_revb_cs_decode.py --rom /path/to/revb.bin --output-dir /tmp/cs-decode
python tools/trace_revb_cs_indexed.py --rom /path/to/revb.bin --output /tmp/cs-indexed.json
python tools/verify_revb_cs_decode.py --rom /path/to/revb.bin
```

Run these commands from the repository root. Full-image tools reject the wrong
hash and never write the input BIN. Explicit output arguments control writes;
the verifier compares recorded witnesses unless `--output` is supplied.
To intentionally update committed extraction tables, select this directory as
`--output-dir` and review the diff. Local data must remain aligned with its
image, conditional CPU-layout interpretation and bounded test scope.

Recorded verification reconstructs only the committed local excerpts, reruns
the instruction witnesses, matches extracted stores and checks CSV range/
translation consistency. It checks the recorded whole-image scan's identity and
binding inventory; it does not regenerate that scan from incomplete bytes.
Use the exact full image for a fresh 132-entry abstract analysis. Unknown/formal
indexed pointers, interrupt histories, stack corruption, hardware backing and
external aliases retain their stated qualifications.
