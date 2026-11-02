# SCI/ALDL transport, session timing and boot seeds

This batch adds16 public routines and replaces three task boundaries. The tree
has277 routines:141 implemented outlines,108 algorithms and28 dependency
boundaries. The serial polling, SCI body and post-controller boot stage now run
resident C without their former task bindings. Their task IDs remain reserved.

## Entries and stops

| Stock scope | C entry | Responsibility |
| --- | --- | --- |
| F7EA..F820 | `pcm_sci_irq` | Literal RX → TX-empty → TX-complete arbitration and final driver release |
| F90B..FA5A | `pcm_serial_receive` | Status/data capture, checksum accumulation, ID/length/payload/accept routing |
| F927..F939 | `pcm_serial_find` | Normal51BF or factoryFBD7 linked descriptor search |
| F96B..F9B5 | `pcm_serial_payload` | Command/page selection and immediate RX stores |
| F9BE..FA27 | `pcm_serial_accept` | Retained command/service copying and reply admission |
| F822..F90A | `pcm_serial_transmit` | Header, command echo, payload, checksum and completion |
| F86E..F8DE | `pcm_serial_next` | Flat, live-pointer and requested-address data selection |
| F8E6..F8F3 | `pcm_serial_send` | Data write followed by fresh checksum/count updates |
| F8F4..F90A | `pcm_serial_finish` | Clear transfer state, drain status/data and arm TC |
| FA28..FA4C | `pcm_serial_start` | Capture descriptor, emit ID, enable driver and arm TX |
| FA4D..FA5A | `pcm_serial_abort` | Clear descriptor/count/checksum and restore receive control |
| F5E8..F64D | `pcm_serial_poll` | Optional broadcast lookup, deferred flag, precopy and launch |
| F781..F7E9 | `pcm_serial_idle` | Session expiry and service-age/expiry words |
| F637, F7A2, F813, FA3B sequences | `pcm_serial_driver` | Shared3FFC word read,11-cycle gap and low-byte bit2 update |
| 717F..7189 | `pcm_serial_clear_ram` | Callable boot slice clearing0360..03FE and retaining03FF |
| 7431..7458 | `pcm_reset_serial` | Phase/BLM/startup/COP/shadow seeds, conditional REF age |

The IRQ comparison stops beforeF821 RTI. The target must provide masked entry,
the actual interrupt frame and ABI restoration. Calling a host body does not
synthesize that frame. Driver helpers retain the caller's mask precondition;
ordinary broadcast and idle paths issue the actual SEI/CLI assignments.

## State and logical addressing

`PcmSerial` owns count/checksum/descriptor, session/clear-edge bytes, last ID,
length/companion/receive age, duration words,34 retained RX bytes and the engine
and transmission command bytes. Shared003B flags reuse the existing monitor,
engine-service and transmission-service owners. Three small address helpers bind
these fields directly, without a second RAM image.

Other logical addresses use the explicit platform read/write interface. Its
provider must bind nonserial RAM to the canonical named `Pcm` owners and supply
the chosen ROM/device view. The native struct layout is not a factory RAM map.
For example, accepted038F..0398 service stores must update existing controller
service flags/values through that provider. Word reads retain callback width;
a word crossing an ownership boundary is supplied as one provider read. This
batch supplies a coherent host-test provider, not the target address-space port.
Descriptor tables and service thresholds are read through this same interface;
no native C pointers are substituted for16-bit logical addresses.

The ROM authority is the recorded BMHM image with SHA256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The fixture loads its full4000..FFFF contents, including descriptor graphs,
command/page tables and data pointers. File padding below4000 is not runtime RAM.
Stock51BB/51BD areFFFF/0000. The33-byte broadcast schedule at518F is zero in
stock; synthetic schedule words exercise the dormant paths without altering
production defaults. Phase indexes that schedule as an unscaled byte offset.

## Retention and transaction details

RX status and data reads precede receive-age clearing. Error bits0E abort before
checksum addition. F4/F5 session bits latch on the ID byte, before length and
checksum acceptance. Payload stores occur as bytes arrive; abort preserves those
stores, prior command bytes and the last accepted ID. A valid N=0 frame uses the
retained command byte. The accepted length gate is0..34, without extra
per-command size validation. Page selectors3..255 normalize to0 before storage.
Normal command04 copies up to11 bytes; factory mode copies the accepted length.
The code does not invent a factory callback whitelist or execute uploaded code.

TX count and offset arithmetic wraps as bytes. Command03 header adjustment uses
the literal signed ASRA result, including malformed old lengths. The addressed
command echo takes priority over the payload length. Payload/checksum selection
precedes a pending word companion. A selected1000..3FFF address uses one word
read, normal-mode address masking and a saved low byte; flat replies remain byte
reads. Thus successive fields can observe changing live state while a word's
companion remains from its first sample. Checksum/count update after the data
write samples the current fields, preserving callback effects.

Finishing a frame arms TC with40 and leaves the driver and busy flag for the
subsequent TC interrupt. Starting an addressed reply does not invent a busy-bit
set. The driver changes low3FFD.2 while preserving high3FFC.2 fuel triggering.
The11-cycle delay binding preserves the source JSR/RTS gap as a host contract;
it is not a measured bus turnaround time.

Session expiry clears only the source-selected session, command and clear/busy
bits. It preserves unrelated payload, deferred and companion state. Literal CLI
precedes the duration test, so that test observes fresh controller-service flags.
Counter wrap, threshold equality and the old255 receive-age branch are retained.
Duration comparisons retain the captured increment across the provider threshold
read; a callback can change stored age without replacing that comparison input.

`pcm_serial_find` adds a65536-hop configuration guard for a cyclic supplied
descriptor graph, returning BAD_CONFIGURATION without assigning its output.
This bounded failure is tested separately; it is not claimed as stock behavior
for a corrupt graph. Missing callbacks and failed operations return at their
committed prefix with the current mask, consistent with the other host bodies.

## Boot and remaining work

The historical `reset_serial` name actually denotes7431..7458 post-controller
seeds: phase0E, BLM128, startup counter20, existing21-cell BLM clamp, COP55/AA,
output shadow40, and conditional REF age from4D96. SCI register initialization
is already in the earlier CPU/output stages. The new0360..03FE clear routine
is callable but does not replace the broader working/retained reset boundary.
Neither slice supplies startup assembly, stack setup or retained-memory policy.

The F64E..F780 retained/controller service lifecycle, AE85 input wrapper and its
ordered F781→F64E join remain the next implementation layer. Service requests
are accepted/stored here; clear-edge execution, output-enable cleanup and their
complete scheduled consumers remain separate. Manufacturing admission/upload/
callback execution and factory periodic mode also remain explicit boundaries.
See the [factory serial closure](../../docs/analysis/FACTORY_SERIAL_SERVICE_CLOSURE.md)
for the documented source behavior. Full boot, trap/stack/watchdog handling,
target memory fit and physical8192-baud/electrical behavior require their own work.

## Verification

`serial_test.c` and `compare_serial_rom.py` compare native state and ordered
byte/word/mask/delay transactions with actual HC11 instructions. Cases include
complete normal/factory requests and IRQ-driven replies, all incoming bytes at
the framing/error gates, all SCI enable/status pairs, transmitter count/length
pairs, command bytes, selected-address domains, optional broadcasts, expiry,
callback mutations and representative failed transaction prefixes. The CPU's
private call-stack bytes are excluded from arbitrary-address comparisons; they
cannot establish the future C target ABI. Boot clear executes without a
synthetic return address inside the region being cleared.

The serial suite contains309,610 C/ROM cases and executes all385 scoped
instruction starts, excluding the target RTI boundary. It includes431 selected
failed-operation prefixes,256 retained histories and130,667 selected-address
cases outside private HC11 call-stack bytes. Missing logical bus bindings,
owned serial RAM access and corrupt descriptor-cycle bounds have separate C
contracts. An additional final duration check covers24 callback cases and1,440
session/counter boundaries after making the expiry word's single capture explicit.

Both host routes now have52 entries:26 quick contracts/provenance checks and26
ROM suites. All26 quick checks,190 factory tests,18 simulator tests including
real-ROM boot/run, repository hygiene and17 runnable static builders pass locally
(32 builders intentionally skipped). Earlier long differential suites remain
part of the complete CI run. Publish after local verification; report GitHub
checks as pending and check their completed results before a later merge.
