# Slot7 producers, output shadow and connection probe

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Actual instructions implement the following five calls and return at 7B1B..7B2A:

| Order | Entry | C interface | Current status |
|---|---|---|---|
| 1 | C514 | `pcm_transmission_outputs` | Complete resident output builder |
| 2 | F5DC | `pcm_connection_probe` | Complete signature probe; matching 180C module remains a dependency |
| 3 | 9E99 | `pcm_iac_background` | Complete resident background IAC; see [IAC contract](iac_background_contract.md) |
| 4 | CA6B | `pcm_spark_auxiliary` | Existing complete MAT/PE/knock-gain producer, now called directly |
| 5 | ACA7 | `pcm_shift_lamp` | Explicit `PCM_SHIFT_LAMP` dependency |

Each public routine has its own file. `pcm_slot_07` now preserves this sequence
and stops at the first failed prefix. It no longer calls `PCM_SLOT_07`; that
enum value is retained without renumbering existing task IDs. A platform using
the former whole-slot binding must supply the remaining `PCM_SHIFT_LAMP`
dependency and, if its signature matches, `PCM_CONNECTION_EXTENSION`. The former
`PCM_IAC_BACKGROUND` ID is also reserved and unused by production. Missing bindings
return UNIMPLEMENTED and identify the missing task. Tests alone supply successful
returns and selected state effects for the unfinished bodies.

Slot7 is still selected by the existing 16-slot dispatcher and 160-phase counter.
This connects the actual scheduled CA6B producer rather than supplying its
values inside the spark controller. C9F7 environmental precomputation belongs
to slot4's alternating group and remains separate work. Other C514 owners in
slots3/B/F remain inside their existing broader dependencies; this change does
not inject partial calls into those unfinished wrappers.

## C514 output construction

| Factory location | C state | Use |
|---|---|---|
| 00D9,004C | `transmission.selected_gear`, `output_shadow` | Raw byte index and shared board-output shadow |
| 039A.6,039B.6 | `current_service_enable`, `current_service_value` | Raw current-enable service selector and value |
| 0099.3 | `inhibit_flags` | Normal current-enable inhibit |
| 001C.1,001D.7 | `fault_flags_primary`, `fault_flags_secondary` | Live fault gates |
| 0086.0 | `driver_inhibit` | Separate bit from existing profiling0086.6 |
| 008E.7 | `output_fault_flags` | Normal current-enable inhibit |
| 0126,012B | `tcc_command`, `tcc_lower_limit` | Command sample and unsigned comparison limit |
| 008A.2,008B.0 | `tcc_flags`, `tcc_state` | Qualified greater-than indication |
| 400F.6 | Existing `calibration.mode_f` | Skip the electronic state/publication branch when set |
| 306A | `PCM_TCC_COMMAND` | Ordered write16 of7F00 plus the sampled command's high byte |

First read D9 and B319[D9]. Replace 004C with
`u8((old004C & FC) + pattern)`. The operation is an addition, with no mask on
the returned pattern. The normal zero-based gears0..3 select01,00,02,03, so
their other shadow bits are preserved at this step. A different raw byte index
can return a value with high bits and can wrap the addition.

Next choose current-enable004C.5. If039A.6 is set, use039B.6 directly. This
selector does not require003B engine-service qualification and bypasses the
normal inhibit gates. Otherwise enable only when0099.3,001C.1,001D.7,0086.0
and008E.7 are all clear. Update only004C.5 after the pattern addition.
The builder does not latch004C to3062; F411 is the separate later owner.

With400F.6 set, return at this point. Retain008B and306A. Otherwise clear008B.0,
sample word0126, and set008B.0 only when that word is strictly greater than
word012B as unsigned16 and008A.2 is set. Equality leaves the bit clear. Finally
write306A=`7F00 | high(sampled0126)`. The low software command byte is not sent
to this peripheral. The full command remains the comparison input.

A failed write retains the preceding shadow and008B changes. The hardware
fixture keeps the previous peripheral word for a failed operation. A callback
changing0126 during the write cannot alter its already-evaluated argument.
This is a source-level ordering contract, not a physical current/polarity proof.

## Raw-index backing and source profiles

The ROM applies an unclamped byte index. The default
`PcmTransmissionCalibration` therefore supplies a 256-byte immutable view of
B319..B418. Its first four bytes form the normal gear-pattern table; the
remaining 252 bytes include neighboring data and executable bytes. This explicit
read view preserves every raw index without asserting that the upstream gear
producer admits values beyond3. These bytes are not256 independent factory
calibration parameters and do not force our future executable/calibration layout.

The descriptor carries a pointer and backing length. Missing root/profile,
null backing or an index beyond a supplied profile returns BAD_CONFIGURATION
before changing state or hardware. Shorter custom profiles can deliberately
limit their supported index domain. The default permits every byte index.
The source defaults verify all 256 backing bytes and shared 400F=10 against stock.
The earlier 1,197-byte spark fixture remains independently verified.

The new named transmission state is cleared by the existing host reset outline.
This does not supply the still-unfinished target RAM/retained-reset stages or
establish final target storage addresses.

## F5DC connection gate

Read a 16-bit word from CPU1800 on each admission. Only exact 7E18 calls180C.
This recurring probe has no 0086.6 requirement: it can reach a module that
enables or disables that flag. An absent/nonmatching signature returns after
the read, retaining the flag. A failed read stops before module admission.
A matching signature with no module binding returns UNIMPLEMENTED and records
`PCM_CONNECTION_EXTENSION`.

The probe needs no calibration. Its read is an explicit platform transaction;
it does not establish memory backing, writability, a loader or an update protocol.
The recorded all-zero readback is one nonmatching sample, not a replacement
for runtime reads. The actual 180C body and its register/stack/CCR machine ABI
remain unsupplied. The C task signature only defines the new source interface.

The kernel fixture verifies both late activation and deactivation in a real
phase7 periodic pass. The same pass's existing profiling tail sees the new
flag value and retains previous peaks when disabled. The real background IAC and the
shift-lamp dependency run in order around the real CA6B calculations. No missing body is
silently treated as success in production.

## Verification and remaining work

The new suite adds 400,081 compiled-C/ROM comparisons: 196,608 raw-index/shadow
cases, 96,512 command/comparison/publication cases, 36,352 service/inhibit/option
cases, 65,536 signature cases, 3,872 joined/callback witnesses, 945 failed prefixes
and 256 history steps. All 43 instruction starts in C514..C56E, F5DC..F5E7 and
7B1B..7B2A execute. Tests compare mapped state, ordered I/O widths, dependency
admissions, mask state, missing-task identity and completed local ROM frames.

The histories explicitly supply a subsequent normal spark call at phase8 after
slot7. They check retained producer/consumer effects under chosen intervening
inputs; they do not implement the intervening input pipeline or change factory
cadence. This original slot7 suite alone links a test-only9E99 boundary; ACA7
and180C returns remain fixtures, as do subsequently enabled180F/1812 hooks. The
new [IAC suite](iac_background_contract.md) executes the real9E99 body within
slot7 and its following normal call. The kernel's full160-phase regression also
runs the real background body, verifies changed target/kicker state and admits
the shift-lamp dependency ten times, with the former whole-slot and IAC bindings
absent in activation tests.

The inventory is 161 public routines: 73 implemented outlines, 41 dependency
boundaries and 47 algorithms. Both host verification routes include 32 CTest
entries. The9E99 background path is now implemented. The [slow IAC](iac_slow_contract.md) now runs in slot9. Next are main IAC
and its step driver, alongside ACA7's shift-lamp body. Other producers, target assembly,
native ABI, memory/stack fit and physical peripheral timing remain separate work.

See the [spark terms](spark_terms_contract.md),
[adaptive spark](adaptive_spark_contract.md),
[resident controller](spark_controller_contract.md),
[transmission](../../docs/analysis/FACTORY_TRANSMISSION_CONTROL.md) and
[optional behavior](../../docs/analysis/FACTORY_JOINED_STATE_AND_OPTIONAL_BEHAVIOR.md)
contracts.
