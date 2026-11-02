# Retained service commands, diagnostic clears and the scheduled tail

This batch adds 11 public routines. The tree now has 288 routines: 151 outlines,
109 algorithms and 28 dependency boundaries. The former whole transmission-input
boundary becomes an ordered wrapper with an explicit earlier-prefix dependency;
its later idle/service work now runs resident C. One public routine owns each file.

## Entries and interfaces

| Stock scope | C entry | Responsibility |
| --- | --- | --- |
| F326..F332 | `pcm_diagnostic_checksum` | Negative byte sum of retained age0014 and nine bytes0013..000B |
| F333..F376 | `pcm_diagnostic_clear_engine` | Engine/common keep masks, selected flags/counters, checksum refresh |
| F380..F3DA | `pcm_diagnostic_clear_transmission` | Separate keep masks and counter footprint, checksum refresh |
| F64E..F676 | `pcm_service_status` | Ordered diagnostic input reads and independent0130/0131 publication |
| F677..F714 | `pcm_service_transmission` | Transmission04 admission, gear/TCC/adaptive/pressure fields and cleanup |
| F715..F738 | `pcm_service_engine` | Engine04 admission and qualified BLM-reset edge |
| F739..F769 | `pcm_service_clear` | Ordered engine/common and transmission clear edges |
| F76A..F77F | `pcm_service_cleanup` | Final engine session/duration cleanup |
| F64E..F780 | `pcm_serial_service` | All five service stages, preserving intermediate side effects |
| AE9D..AEA3 | `pcm_serial_service_poll` | Consecutive F781 idle expiry then F64E service processing |
| AE85..AE9C | `pcm_transmission_input_prefix` | Explicit dependency for all eight earlier callees |
| AE85..AEA3 | `pcm_transmission_input` | Prefix dependency followed by the resident scheduled tail |

The prefix covers AEA4, B018, B089, C483, B1F0, B23C, B2C9 and B2ED in source
order. It must supply all that work; an absent binding returns UNIMPLEMENTED
before idle or service processing. The old TRANSMISSION_INPUT task ID is reserved
and unused. The new prefix task ID is appended, preserving older task indices.
A successful fixture prefix demonstrates the wrapper order and returned effects,
not execution of those eight unported bodies. Factory mode remains separate.

## Canonical state and the logical-address provider

The existing serial session, command, clear-request, edge and duration owners are
reused. Runtime003B engine/transmission-service flags are now explicitly volatile,
consistent with their shared-byte use; this alone does not provide atomicity.
New transmission fields own0103 service gear,010A TCC,0111 pressure,0118 state,
011A adaptive flags and0130/0131 packed diagnostic status. A system field owns
retained diagnostic checksum0015. Service gear0103 is separate from ordinary
selected gear00D9. Existing controller flags, BLM cells and spark values keep
their current owners.

Foreign logical byte reads/writes use the address-space interface established by
the [SCI/system batch](serial_system_contract.md). Its provider must bind all
relevant named state coherently and supply other RAM, ROM and device semantics.
The new fixture expands those bindings for EST/knock fault latches, the output
inhibit, transmission fault/status fields and spark service amount. Unported
fault/counter bytes remain supplied logical RAM. There is no second production
RAM image, native-layout map or newly inferred physical RAM window.

The clear masks at F377..F37F and F3DB..F3E3 and the first three solenoid patterns
at B319..B31B are read from the supplied ROM view. Tests load the SHA256-verified
BMHM4000..FFFF image. Stock solenoid patterns are01,00,02; a nonmatch selects
gear4 without reading a fourth entry. Source calibration definitions and target
placement remain independent.

## Diagnostic clear footprints

The checksum helper reads0014 down through000B once each, subtracting with byte
wrap. It returns a value and leaves its output unassigned on a failed read.
The two clear routines store that result to0015 only after their earlier work.
Neither clears retained age0014.

Engine/common clear iterates X=9..1, updating retained X+0A, live X+15 and
candidate X+55 in that order. Each bank update rereads the corresponding keep
mask, three reads per index. It then clears0004.7,0044.7,0072.0,006F.4 and0070.0,
zeros001F,0020,0817,021C and081C, and refreshes0015. Actual instruction bytes
resolve the listing's misleading unprefixed15/55 store operands.

Transmission clear updates only retained X+0A and live X+15, rereading its mask
for each bank. Candidates0056..005E survive. It clears0094 bitsF0 and008E.7,
then zeros001F..0024,0026..002D,002F..0031,0182..0185 and0032..0034 in that
order. Counters0025 and002E survive. This is neither a blanket erase nor the
same operation as engine/common clear. No SEI/CLI is inserted into either clear;
“keep mask” describes data masks, not an interrupt critical section.

## Admission, updates and cleanup

Status0130 commits before the independent0131 read sequence begins. Failed
later reads retain the first result. Both use the actual disjoint masks and
wrapped additions from the ROM.

Transmission04 requires session0042.1 and zero036A. Enable/value pairs039A/039B
bits08 and10 build the two-bit solenoid pattern. With neither enable bit set,
prior0103 is retained.039E.7 qualifies copying039F to010A; an inactive selector
retains the earlier value.03A0 is read separately for adaptive bits6 and7, with
two stores to011A.03A1 always writes0111 on this admitted path. The source's
unconditional011A tail also preserves the captured A value if a supplied state
mutation clears the active flag before F6CF. Subsequent transmission cleanup
zeros0399,010A,0103,0111 and0118 and clears003B.3 when ownership is lost or036A
is nonzero. It retains011A and the raw payload suffix.

Engine04 with session0042.0 sets003B.4 even when036A is already nonzero. A rising
0391.4 request resets all21 BLM cells through the existing F280 helper;0045.4
latches completion. Rearm occurs only inside this qualified engine04 branch.
A selector01 pass therefore retains the earlier BLM edge latch.

Engine/common clear request003B.1 takes priority over the active-engine0391.6
read.0045.7 suppresses a repeated clear. Transmission request003B.0 uses its own
0045.6 latch. Latches set only after their clear routines finish; a failed foreign
access retains both its completed data prefix and the old edge bit. Low requests
rearm their corresponding edges. Engine cleanup occurs last, clearing003B.4,
038E and0044.2 on session loss or duration expiry while retaining other payload.

The scheduled wrapper preserves F781 immediately before F64E. Idle expiry can
clear0045.7 while active003B.4 and held0391.6 remain, so F64E may clear engine
faults again before removing engine service. BLM does not repeat on that route,
because idle expiry already cleared038E. Packet acceptance can occur between
those two calls; tests include a final accepting-checksum IRQ in that window.
Service time units remain admitted F781 calls, not declared milliseconds.

## Descriptor reread and joined verification

The expanded foreign-data trace exposed a transport detail at F872/F876: when
the80 format test fails, the40 test rereads the descriptor byte. `pcm_serial_next`
now retains that second read.432 cases mutate the provider byte between those
tests, in addition to normal packet traces. No new protocol whitelist is added.

The service suite contains80,142 compiled-C/ROM comparisons across all198 scoped
instruction starts. It includes1,434 selected failed-operation prefixes,256
retained histories, all65,536 solenoid enable/value byte pairs, nonzero prior
outputs, repeated clears and896 packet/service/checksum-window/spark-consumer
joins. Foreign byte accesses include selected RAM and ROM data; instruction
fetches and native field operations remain distinct. Supplied ordinary IRQ entry
sets I for the SCI body and restores the prior I on successful return. The
actual target frame/RTI ABI remains unimplemented.

The transport regression also passes44,799 cases across its385 scoped starts.
Both host routes now register54 tests:27 quick contracts/provenance checks and27
ROM suites. The complete quick gate,190 factory tests, repository hygiene and
17 runnable static builders pass locally, with32 builders intentionally skipped.
Older long differential suites remain in the full CI run.

The remaining system work includes factory admission/recurring execution,
retained boot/runtime diagnostic stages and target startup/interrupt/backend
interfaces. The eight earlier transmission callees still need resident bodies.
This batch builds on [merged transport PR #29](https://github.com/snow663/7427HWContract/pull/29).
Check this batch's completed GitHub results before merging it in a later step.
Do not wait for Actions in the implementation turn.
