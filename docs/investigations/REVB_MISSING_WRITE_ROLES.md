# Rev B: roles for the 92 previously unnamed write sites

Authority: exact Rev B SHA-256
`e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
This closes the role-naming follow-up from the [read/write audit](REVB_READ_WRITE_AUDIT.md).
All 92 seed instruction sites now have a described function. Naming a retained
instruction does not establish that its path runs with the current calibration.
No BIN, XDF, calibration, OEM workbook or simulator behavior changes.
TS00 truck testing/fine-tuning remains the active firmware checkpoint.

| Kind | Sites | Ownership result |
|---|---:|---|
| Fixed global operands | 80 | Named counters, flags and bank bytes. |
| Bounded global array operands | 9 | Nine-byte diagnostic banks and the 16-word dispatcher timing array. |
| Stack-local operands | 2 | Saved/intermediate words in EST and lag calculations. No absolute RAM owner assigned. |
| Descriptor-selected copy | 1 | Serial staging template with a runtime destination. Normal released broadcast schedule is null. |

The maintained read and write books each gain **86 RAM role entries**. Existing
values and original OEM descriptions are preserved. The read RAM tab now has
583 entries; the write RAM/register tabs have 724/83 entries. Original-role
descriptions for retired code use the recorded factory opcode/diagnostic
contract, with current use separately qualified. This is not a new full-OEM-BIN
analysis or certification of every inherited label.

## Diagnostic state has three separate lifetimes

| Range | Name | Function |
|---|---|---|
| `$0016–$001E` | Live diagnostic fault banks | Current monitor results and boot/hardware fault conditions. Most of these already had names. |
| `$0056–$005E` | Persistence-candidate banks | Faults waiting for central qualification. An existing candidate set is intersected with enabled live faults. |
| `$000B–$0013` | Retained diagnostic log banks | Qualified candidates are ORed into this history, then candidate bytes are cleared. Retained age/checksum and explicit clear paths govern its lifetime. |

The nine bytes use the same bank ordering. At `$E14A`, the central routine
seeds candidates from enabled live faults. `$E16B` intersects old candidates
with enabled live faults; it does not add a newly appearing fault into the
existing set. `$E19F` unions qualified candidates into retained history, and
`$E1A1` clears the candidates. `$DD32` clears aged retained history.
`$F33F/$F34D/$F38C` are masked diagnostic clear operations on those arrays.

The engine-only cleanup explicitly masks or clears removed subsystem bits.
That does not remove the shared bank loops. Bank 5, containing the program,
battery, pump-feedback and ADC fault positions, is not included in that cleanup
mask sequence and is not labeled as cleared by it. The ROM flash-code mapping
names table positions; it does not prove every position has a monitor.

## Counters and flags now have specific names

| Address or group | Established role |
|---|---|
| `$0004.2` | Background observation that the RAM-refresh request is still pending. |
| `$0005.4` | Boot configuration/program-validation failure. |
| `$000F.5`, `$001A.5` | Retained and live program-validation fault positions, DTC51. |
| `$001A.2/.3/.4` | Pump-feedback DTC54 and battery-threshold DTC53/DTC52 faults. |
| `$003A.1–.5` | Program-check failure, CONFIG mismatch, stack-range failure, stack-fill disturbance and dispatcher overrun/resume latches. |
| `$001F/$0020` | DTC21/DTC22 retained TPS-fault recovery budgets. These are distinct from entry-qualification counters. |
| Selected `$0021–$0031` slots | Retired diagnostic recovery budgets, still touched by explicit diagnostic clearing. |
| `$0032–$0034` | Former gear-specific DTC89 long-shift qualification counters; current explicit clears remain. |
| `$015F` | DFCO exposure/recovery counter used by the O2 activity diagnostic. |
| `$0160/$0161` | DTC14 low-ADC and DTC15 high-ADC coolant qualification counters. ADC polarity is kept explicit. |
| `$0162/$0163` | DTC21 high-raw-TPS and DTC22 low-raw-TPS qualification counters. |
| `$0169–$016A` | DTC52 high battery-sample qualification word. |
| `$016B` | DTC53 battery-threshold qualification byte. The actual predicate is also a high-side comparison. |
| `$0182–$0185` | Former DTC37/DTC38 brake/speed episode stage counters; current explicit clears remain. |
| `$0817/$081C` | Former VSS-buffer and manual-option VSS diagnostic counters; current explicit clears remain. |
| `$0856` | VATS authorization-failure qualification counter, DTC46. |

The DTC53 label deliberately does not claim a low-voltage predicate: `$EA8C`
compares the battery sample, and `$EA8E` takes BHI into the fault-qualification
path. A familiar DTC title cannot reverse the actual branch. Counter increments
are admissions, not independently established seconds.

Two legacy recovery slots, `$0026/$0027`, have a clear counter/storage role
but no proved implemented monitor identity. They are named **Legacy diagnostic
recovery slot A/B**, with that limitation preserved. The old source comments
alone do not justify assigning active DTC66/DTC67 monitors to them.

The naming pass does not mark a retired monitor active merely because its
counter is cleared. Read-side omitted roles and write-side explicit cleanup
descriptions remain distinct. The detailed address catalog contains every
new row and its original-role/current-use split.

## Scheduler and stack housekeeping

| Address | Name | Function |
|---|---|---|
| `$027E–$027F` | Ignition-off fuel-pass counter | The fuel task reads it, counts admitted ignition-off passes and resets it on the running path. |
| `$029B–$029C` | RAM-refresh scan cursor | Advances through admitted refresh blocks and returns to the initial cursor state at completion. |
| `$02D1–$02D2` | Minimum observed stack-fill scan boundary | Saves the lowest boundary found by scanning the stack-fill region. This is a scan observation, not an exact instantaneous SP reading. |
| `$02D3–$02F2` | Dispatcher slot elapsed-time maxima | Sixteen word entries, selected by twice the low nibble of the phase counter. Only a greater observed elapsed count replaces an entry. |

The timing array update at `$7A77` is gated by `$0086.6`. Its coordinate is a
timer count relative to the programmed dispatcher compare, with an extra
period adjustment on the overrun path. It is not an RPM, MAP or calibration
table. The names do not claim these measurements are always enabled.

The write at `$ABA0` updates an **EST timing candidate on the current stack**.
The preceding PSHB/PSHA/TSX sequence establishes its local word. `$F449`
updates a **saved intermediate lag-state word on the stack**, established by
PSHX/TSX in the 16-bit lag helper. Controlled cases move the starting stack
pointer and observe both write addresses move with it. Neither site is given
a fixed variable row in an address workbook.

## Serial staging template and the released schedule

At `$F627`, a byte read through a descriptor-selected source pointer is copied
to the location in Y. Y advances; the descriptor cursor advances to the next
source-pointer word. Its role is **descriptor-selected serial payload staging**.
A synthetic two-source descriptor confirms that copy behavior without claiming
an admitted released transaction or a permanent destination buffer.

The normal entry `$F5E8` selects an offset using phase AND `$1F`, adds that
**byte offset** to `$518F`, and loads a descriptor word. All 32 possible loads
are zero in the exact released image. Checking them requires the 33 bytes
`$518F–$51AF`, because neighboring word loads overlap. All 32 controlled normal
entry cases therefore take the null-descriptor exit before `$F627`.

This qualifies the ordinary broadcast staging path. Requested ALDL replies use
the separately documented reply path; their operation is not determined by
this empty broadcast schedule. Arbitrary direct entry, modified descriptors
and uploaded code remain outside this normal-entry argument.

## Evidence and verification

The [role evidence directory](../../maps/maintenance/revb_write_roles/README.md)
contains all 92 site roles, 86 address descriptions, the historical seed list,
exact selected current bytes and 47 scoped CPU cases. These exercise candidate
seeding/intersection/logging, age and masked clears, elapsed maxima, stack-local
words, all broadcast selectors and the descriptor-copy template.

The write inventory now reports separately:

- No writer site lacking both a named address reference and a traced routine role.
- Three sites without fixed/global address rows, correctly represented by the
  two stack-local roles and descriptor-selected copy.
- Remaining qualifications on legacy monitor identities, generic indexed
  contexts, interrupt histories and physical hardware behavior.

```sh
python tools/verify_revb_write_roles.py --rom /path/to/revb.bin
python tools/verify_revb_write_roles.py --check-recorded
python tools/audit_revb_rw.py --rom /path/to/revb.bin
python tools/audit_revb_rw.py --check-recorded
python tools/trace_revb_reads.py --check-recorded
python tools/build_custom_xdf.py --check
```

`--record` intentionally refreshes generated evidence when supplied the exact
BIN. Recorded mode validates catalog instructions, named owners, workbook roles
and selected instruction behavior. It does not regenerate full-image rooting
or certify every semantic name from incomplete excerpts. Controlled storage
does not model peripheral side effects, electrical responses or truck behavior.
