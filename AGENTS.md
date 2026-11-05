# Address-register maintenance

Use the two root workbooks as address/role references alongside the ROM-backed
contracts. Actual image bytes and reviewed traces take precedence over a label.

- `7427_Address_Register_OEM_BMHM.xlsx` is the preserved OEM BMHM $31 baseline.
  Do not change its roles to match modified firmware.
- `7427_Address_Register_0.3.12.xlsx` is the maintained non-OEM register. Update
  this same file as traces establish new addresses or firmware changes their use.
  Keep the filename stable across later BIN revisions.

Both have ROM reads, RAM reads and ADC-HW reads tabs. The OEM columns are Address
and Role. The non-OEM columns are Address, OEM role and Current use:

- Blank Current use: OEM role retained.
- Literal `omitted`: original software role removed. Preserve the row.
- New role text: address reused. Preserve the OEM meaning in column B.

After each trace, add newly established locations and named bit fields to the
appropriate non-OEM tab. Sort by numeric hexadecimal address and bit number,
keep addresses as text, and avoid duplicate rows. For a newly allocated address,
record its established original/reserved role in column B and its new use in C.
Never mark a shared role omitted merely because one consumer was removed.
An omitted hardware role means the firmware use is removed, not the register.

Keep sheets limited to address and role/use descriptions: no actual bytes,
opcodes or calibration values. Calibration-value changes alone do not alter an
address's role. Keep source-only labels qualified until confirmed by a trace.
Record image identities and supporting trace evidence outside the workbook tabs.
Update the snapshot identity below when the maintained register advances.

Initial snapshots (2026-11-05):

- OEM BMHM SHA-256:
  `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
- Non-OEM: `0.3.12_engine_only_spark_idle_revA.bin`, SHA-256:
  `d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e`.
- Each register starts with 682 ROM, 483 RAM and 42 ADC/HW entries. These are
  named data/table starts, bit fields, pointers/vectors and readable hardware
  locations, not a byte-by-byte map or proof of full semantic coverage.

The pending deceleration-spark change is not part of this snapshot. Do not
record proposed changes as implemented.
