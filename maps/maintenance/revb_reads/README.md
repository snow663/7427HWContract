# Rev B read extraction

Read the [resource and operation guide](../../../docs/investigations/REVB_READ_RESOURCES.md)
for the address map, functional interpretation, ADC caller context and limits.
All records refer to the exact released Rev B SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
No complete BIN is included.

| File | Purpose |
|---|---|
| `READ_SITES.csv` | 2,221 explicit read/RMW instructions, exact bytes, widths, functional groups, finite target ranges and unresolved-context counts. |
| `READ_CONTEXTS.json` | Per-site finite starts/bytes and indexed abstract contexts, including call paths and unresolved/formal expressions. |
| `READ_ADDRESSES.csv` | Finite byte consumers and finite may-writer cross-references; not a last-writer or ownership proof. |
| `HARDWARE_READS.csv` | 108 site/address rows, 34 distinct address/width forms in `$3000–$3FFF`. |
| `RESOURCE_SUMMARY.csv` | Fixed/finite read coverage against the conditionally interpreted CS/EN map; checksum separate. |
| `QUALIFIED_READ_RANGES.csv` | Eight strided checksum read sites for the boot call starting at `$4008`. |
| `IMPLICIT_STACK_READS.csv` | 187 pull/return sites; current stack addresses remain dynamic. |
| `INSTRUCTION_FETCH_RANGES.csv` | Union of rooted instruction-byte ranges, separately classified from data reads. |
| `VECTOR_READS.csv` | 21 vector-word candidates; actual admission/mode selects the vector. |
| `EVIDENCE.json` | Selected exact ROM excerpts for local witness replay, not the full image. |
| `EXECUTION_WITNESSES.json` | 22 bounded CPU cases with instruction fetch distinguished from data/stack reads. Controlled storage does not simulate peripheral read semantics. |
| `REGISTER_UPDATES.json` | Two hardware read-reference additions, before/after workbook hashes, roles and supporting PCs. |
| `SUMMARY.json` | Exact image/reference identities, extraction counts and scope. |

```sh
python tools/trace_revb_reads.py --check-recorded
python tools/trace_revb_reads.py --rom /path/to/revb.bin
python tools/trace_revb_reads.py --rom /path/to/revb.bin --record
```

Run from the repo root. Full-image mode requires the exact 64-KiB hash, reruns
normal-return abstract flow and compares every generated extraction file unless
`--record` is explicitly requested. It never edits the input BIN. Abstract
finite sets are may-effects, not a full proof of feasible paths or physical
aliases; generic parameters and widened/runtime pointers remain explicit.

Recorded mode checks internal consistency and replays scoped instruction
witnesses using committed excerpts. It cannot independently reconstruct the
whole-image sweep, all writer effects, role semantics or abstract contexts from
those excerpts. Its checksum fixture verifies the address walk, not the absent
full ROM's released checksum. Full-image mode checks that released checksum
separately. Read categories overlap and must not be summed as physical capacity.
