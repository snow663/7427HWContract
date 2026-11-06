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

The Rev A Park/Drive trace and source-only manual-idle reports remain historical
evidence. The maintained non-OEM snapshot now advances to the actual Rev B
candidate, `0.3.12_engine_only_manual_idle_revB.bin`, SHA-256:
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
See [the release trace](docs/investigations/MANUAL_IDLE_REVB_RELEASE.md).
The single controller, idle-approach deceleration-spark gate and cold-idle
base-table changes are implemented in that image. It is a software-validated
development candidate, not a truck-validated calibration. Preserve the original
Rev A BIN/XDF as a separate rollback pair and leave both OEM books unchanged.
The proposed map remains a historical design document; the maintained books
and new image trace govern actual addresses. Retained shared reads and explicit
cleanup writes must not be confused with removed operational roles.

Maintain the image-specific [custom XDFs](definitions/README.md) with their corresponding
program layouts. The development definition is not valid on Rev A. A change to
the manual-idle source/layout requires review of its calibration mapping and
the definition identity contract; regenerate with `tools/build_custom_xdf.py`
and run its verifier/tests. Keep the uploaded source XDF attribution and the
preserved compressed source unchanged. Do not expose new executable bytes as
tuning parameters, or invent enable switches for code without one.

For custom-ROM tuning simplifications, follow the ordered
[trajectory and active checkpoint](docs/WORKING_STATE.md#tuning-simplification-trajectory).
Keep one step active and update its status, PR/image evidence, remaining
validation and next action before advancing. Preserve queued work across turns;
the separate factory-equivalence milestones do not imply custom-ROM completion.
