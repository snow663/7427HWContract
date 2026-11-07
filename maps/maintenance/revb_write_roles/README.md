# Rev B formerly unnamed writer roles

Read [the role guide](../../../docs/investigations/REVB_MISSING_WRITE_ROLES.md).
All records concern exact Rev B SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.

| File | Content |
|---|---|
| `SEED_SITES.csv` | Historical 92-site list from the preceding audit. |
| `SITE_ROLES.json` / `.csv` | Reviewed name, kind, instruction bytes, qualified global owners or non-global role for every seed PC. |
| `ADDRESS_ROLES.json` | 86 established address/bit roles and their read/write Current use split. Original roles for retired monitors use recorded factory evidence. |
| `REGISTER_UPDATES.json` | Latest workbook and write-evidence before/after identities; chains to the prior audit journal without rewriting it. |
| `EVIDENCE.json` | Selected exact code/table excerpts, including all 33 bytes needed by the 32 overlapping broadcast word reads. |
| `EXECUTION_WITNESSES.json` | 47 bounded controlled-memory CPU cases. Synthetic descriptors/gains are explicit fixtures. |
| `SUMMARY.json` | Role counts, image identity and remaining ownership qualifications. |

```sh
python tools/verify_revb_write_roles.py --check-recorded
python tools/verify_revb_write_roles.py --rom /path/to/revb.bin
python tools/verify_revb_write_roles.py --rom /path/to/revb.bin --record
```

The JSON role catalogs and historical seed are reviewed inputs, not regenerated
semantic discoveries. Full-image mode verifies actual instruction bytes and
rooting; recorded mode decodes committed instructions and replays scoped cases.
Neither supplies full interrupt/alias/hardware closure. Stack-local and
descriptor-selected writes retain dynamic addresses. Two legacy recovery-slot
monitor identities remain unproven; their counter/clear roles are named.
