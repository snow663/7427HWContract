# Address-register maintenance

Use the four root workbooks as address/role references alongside the ROM-backed
contracts. Actual image bytes and reviewed traces take precedence over a label.

- `7427_Address_Register_OEM_BMHM.xlsx` is the preserved OEM BMHM $31 baseline.
  Do not change its roles to match modified firmware.
- `7427_Address_Register_0.3.12.xlsx` is the maintained non-OEM register. Update
  this same file as traces establish new addresses or firmware changes their use.
  Keep the filename stable across later BIN revisions.
- `7427_Write_Register_OEM_BMHM.xlsx` preserves the OEM write roles.
- `7427_Write_Register_0.3.12.xlsx` is the maintained non-OEM write reference.
  Update this same file as writers are traced, removed or repurposed.

The read workbooks have ROM reads, RAM reads and ADC-HW reads tabs. The write
workbooks have RAM writes and Register writes tabs. The OEM columns are Address
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

For the write reference, distinguish removed operational roles from remaining
initialization, refresh, explicit cleanup and inactive output commands. A removed
role may still receive generic RAM clearing/refresh; keep it `omitted`. A specific
replacement cleanup or output-off write has its own Current use description.
Read-modify-writes belong in both applicable read and write references. A word
start covers both bytes; preserve separately named byte/bit owners when useful.
The early reset INIT write at $103D is a register write, not ordinary RAM.

The initial write evidence is in
[maps/maintenance/write_registers_evidence.json](maps/maintenance/write_registers_evidence.json).
It records role text, writer instruction addresses, exact image identities and
scope separately from the clean workbook columns. Keep it aligned when editing
the write workbooks. Indexed footprints retain their stated caller/state
qualifications; arbitrary upload pointers, stack frames and external hooks do not
become fixed named destinations by assumption. Record unknown register identities
as unresolved rather than guessing their function.

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
- The write registers added on 2026-11-06 each start with 624 RAM and 82 register
  entries, including named bit fields, qualified indexed destinations and reset
  writes. Their reviewed image identities match the snapshots above.

The pending deceleration-spark change is not part of this snapshot. Do not
record proposed changes as implemented.

The [2026-11-06 Park/Drive trace](docs/investigations/REVA_PARK_DRIVE_TRACE_20261106.md)
corrects the former non-OEM `omitted` label at $4F50: the curve still supplies
the startup base target. Normal background target selection uses $FF60. Running
IAC context $0036.1 is forced Drive, while Park cold-state housekeeping remains
and can gate Drive warm snapshots. The maintained books include these findings;
the OEM books remain unchanged. Do not equate a removed normal consumer with a
location having no surviving startup/initialization consumer.

The [manual-idle replacement](docs/investigations/MANUAL_IDLE_REPLACEMENT.md)
is executable C/HC11 source tested only as an in-memory Rev A overlay. No new
BIN exists. Keep the maintained workbooks' snapshot on Rev A. Newly traced
existing $0036 bit fields belong in those books, but future omissions/reuse in
the [proposed address map](maps/maintenance/manual_idle_address_plan.csv) must
not be applied until an actual image release. The OEM books stay unchanged.
