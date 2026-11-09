# ROM validation, retained-state recovery and boot bookkeeping

The 71C3..7392 retained-boot boundary now calls separate C bodies for ROM
validation, retained diagnostic checksum/recovery, adaptive-bank validation and
recovery bookkeeping. The actual next instruction is 7393; the former7392 stage
marker pointed into the preceding STAB operand. RESET_RETAINED remains reserved
and unused. Controller initialization remains the next dependency.

| Scope | C entry | Important behavior |
|---|---|---|
| F2AA..F2FC, rooted X=4008 | `pcm_rom_checksum` | Read4008..FFFF in order; first COP pair after255 groups of8, later pairs after256 groups; each pair is55 thenAA. |
| 71C3..720B | `pcm_boot_rom_validate` | CONFIG0B, checksum/mask identity, AA escape, separate code51 failure publication and captured ADC wait. |
| 720C..723E | `pcm_boot_retained_validate` | F326 checksum comparison; exact three clear ranges on failure; TPS-zero and21-cell BLM seeds;0086.3 publication. |
| 723F..726A | `pcm_boot_adaptive_validate` | Backward52-byte cumulative sum, nonzero intermediate observation, ascending80 fill on rejection. |
| 726B..7392 | `pcm_boot_recovery` | Initial spark word,19 distinct recovery thresholds, qualified extra0031 update, separate bit clears and three zero-B stores. |

The checksum entry deliberately exposes only the rooted4008 caller, rather than
claiming a general arbitrary-start checksum API. Five generic byte-prefix starts
F2B9/F2BB/F2BD/F2BE/F2C0 are outside that caller's reachable contract. A failed
read/COP write preserves the caller's output word while retaining prior effects.
The ROM authority is BMHM SHA256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.

ROM failure preserves the 3FFC word read, literal11-cycle JSR/RTS gap and word
write clearing low-bit3. It sets the original live/retained code51 owners,
refreshes0015, then samples082F once. At7208 the source only compares that
captured A value. A sample>=64 hexadecimal therefore returns the explicit
`PCM_BOOT_WAIT_BOUNDARY`; it does not invent ADC resampling or a recovery return.
This new status is appended after the existing status values. Target execution
of the nonreturning loop remains separate from a host C return.

Retained loss clears0000..000A,000B..0035 and029D..034D through the exact F2FD
helper, publishes02F6 as minimum:80, resets all21 BLM cells and sets0046.6. Valid
nonzero diagnostic logs preserve learned state. Adaptive validation is separate:
all-zero52-byte input fails even with a zero final sum. Rejection writes every
byte02F8..032B as80 in ascending order and sets003A.6.

Recovery counters decrement only when nonzero and below their own threshold.
The later0031/live001E.2 test rereads its threshold.0019 bits04 and02 clear in
separate operations. The final0032..0034 stores use B=0 established at726E, not
an assumed arbitrary entry register value. The 01F6 seed remains a distinct
word, with low byte zero.

The logical-address provider must bind the existing named owners and the new
`PcmSystem` diagnostic log/age,22 recovery counters, boot/ROM/configuration/
adaptive/initialized bits and initial-spark word coherently. Shared runtime,
BLM, TPS-zero, profiling and serial owners are reused. No production64KB RAM
array or physical RAM backing is inferred. ROM/calibration bytes are supplied
through the same logical view already required by serial/service processing.

Focused verification passes729 C/ROM cases across253 rooted instruction starts:
identity/configuration gates, checksum/COP order, AA escape, failed prefixes,
captured-sample mutation, valid retained logs, invalid adaptive banks and joined
ROM/retained/adaptive loss histories. The fixture records explicit operand reads,
writes and delays, excluding instruction fetches, generic CLR's discarded helper
read and private03B0..03FF call-stack bytes. Native F280 cell stores are compared
as state effects. This is not a physical bus-cycle or target-stack proof.

The new recovery tests exposed and required the
[unsigned indexed-displacement correction](../../docs/investigations/HC11_UNSIGNED_INDEXED_OFFSETS.md).
Focused CPU and new boot checks run during development. The full source,
simulator and repository regression suites remain queued for the user's
"pull and merge" instruction; earlier whole-suite results are historical.
