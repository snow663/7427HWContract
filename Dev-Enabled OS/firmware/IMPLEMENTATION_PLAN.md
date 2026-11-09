# Dev-Enabled OS — firmware implementation plan

**Status:** Plan only; no target firmware patch, BIN, or XDF produced by this document.  
**Target:** GM 16197427, modified `$31` Rev B image `0.3.12_engine_only_manual_idle_revB.bin`.  
**Pinned parent SHA-256:** `e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.  
**Parent checksum:** `4E78` at CPU ROM `$4006`; **size:** 65,536 bytes, file offset = CPU address.  
**Protocol:** [v0.2 console design](../docs/RevB_ALDL_Developer_Console_Design_v0.2.md).  
**Existing workstream:** [STATUS.md](../STATUS.md).  
**Priority:** A new read-only `$F5` console without changing fuel, spark, idle, interrupt deadlines, or the existing `$F4` OEM engine diagnostic service.

## Architecture / non-negotiable ownership

```text
Android command compiler -> complete $F5 binary request -> SCI receive ISR
        -> isolated developer receive staging -> validate complete frame
        -> 1-command pending flag -> background slot A ($7B39)
        -> bounded handler -> sealed response -> existing SCI TX driver
        -> Android decode, expressions, watch loops, logs, traces
```

- Android owns command syntax, macros, loops, conditionals, symbol names, scaling, polling schedule, and export. The PCM owns only fixed binary primitives and access enforcement.
- Use the **retired `$F5` ALDL identifier directly**, no OEM Mode `$0B`; preserve the original `$F4` request/response logic when no developer session is active. The host will not deliberately run both applications simultaneously.
- Bluetooth module UART remains **9600 8N1**. Do not claim the PCM SCI bitrate equals 9600 until the existing adapter and actual SCI setup are verified; the established adapter provides whatever compatibility is already working.
- SCI ISR must only receive, checksum, stage, queue, and advance TX. **No console parser, loops, serial waits, arbitrary memory writes, or formatted strings** on the PCM. Mainline service bounded to one request.
- Never change ROM/ASIC/HC11 registers through this interface. Phase 1 is strictly read-only except developer-internal protocol state.
- An `FF` ROM byte is a valid HC11 opcode; absence of direct references is not sufficient allocation proof. Never infer physical RAM ownership from the all-`FF` BIN padding below `$4000`.

## Source-backed integration map

| Entry | Observed Rev B behavior | Work |
| --- | --- | --- |
| `$FFD6 -> $F7EA` | Existing SCI IRQ; RX-first arbitration | Preserve entry and low-level error/driver behavior |
| `$F90B`, `$F927` | Byte RX, checksum, descriptor search from `$51BF` | Branch `$F5` into dedicated developer receive state, retaining `$F4` |
| `$53A8`, `$53C9` | Linked `$F5` descriptors | Map their remaining callers, TX triggers and memory ownership before disabling/reusing |
| `$F955–$F963` | Frame payload length `0..34`, encoded `$55+N` | Require developer request `4..34` and full bounded staging |
| `$F96E–$F9AE` | OEM mode handling, descriptor-selected **write before checksum** | Bypass completely for developer payload, including error/abort paths |
| `$F9B9–$FA24` | Checksum acceptance, OEM `$F5` session/command and immediate response | Queue one validated developer request; bypass OEM `$0399` updates and old reply selection |
| `$F822–$F8F4`, `$FA28` | Descriptor-based TX, checksum, shared SCI progression | Select immutable developer TX bytes with existing completion/driver lifecycle |
| `$F781`, `$F5E8`, `$F715` | Session expiry and scheduled communications | Trace every F5-dependent side effect and preserve required F4/watchdog/latch semantics |
| `$3FFC` | Shared external hardware output latch | Preserve masked bus enable/release operations and unrelated engine bits |
| `$7A99 -> $7B39` | Dispatcher slot A = 3 NOP + RTS | Replace NOPs with `JSR DevService` (3 bytes), retain RTS |
| `$7A9B -> $7B3D` | Dispatcher slot B = 6 NOP + RTS | Reserve as optional later short service; **leave unchanged in Phase 1** |

The supplied `FULL_HEX.txt` reconstructs the 64 KiB image with the pinned SHA and its byte pattern shows `$AE85–$C56E` entirely `FF` (5,866 bytes). This is only a **candidate code cave**, not an allocation approval. `$036C–$038D` is a 34-byte OEM RX staging window; `$039A–$03AF` is a 22-byte small-state candidate; `$03B0–$03FF` is stack-sensitive and off-limits unless separately proven otherwise. `$038E–$0398` remains shared; do not reclaim that whole span.

## Required firmware modules

| Module/source | Responsibility and hard boundary |
| --- | --- |
| `src/dev_hooks.asm` | Minimum reversible `$F5` RX/TX branches and slot-A `JSR`; no broad ALDL refactor |
| `src/dev_rx.asm` | One isolated bounded receive FSM, length/checksum/version/magic checks, abort/timeout, RX buffer lock |
| `src/dev_state.asm` | Explicit RAM layout and `IDLE/RX/PENDING/EXEC/READY/TX` transitions; reset and cleanup |
| `src/dev_dispatch.asm` | Bounded command table; full request-argument checks; no user-string interpretation |
| `src/dev_read.asm` | Central PCM-enforced allowlist, byte/word copy with volatile-read policy |
| `src/dev_tx.asm` | Reply size/sequence/status, checksum, prepared immutable payload and TX-done unlock |
| `src/dev_info.asm` | `INFO(selector)` returns build token, protocol version, capabilities and counts |
| `src/dev_snapshot.asm` | Phase 2: published groups captured at proved producer boundaries; not a generic GATHER |
| `src/dev_trace.asm` | Phase 2: fixed-cost event insertions, bounded ring/overrun and host-paced fetch |
| `patches/build_dev_image.py` | Reproducible SHA-pinned overlay, ROM checks, original-byte assertions, checksum repair, diff manifest |
| `tests/` | Host codec, instruction/flow, serial ISR, scheduling, ROM simulator, differential and negative tests |

The names above are **planned paths**. They are not claims of existing assembled modules.

## Protocol v1 implementation contract

Frame: `F5 LENGTH D6 01 SEQ CMD [ARGS] CK`, reply uses `(CMD|80)` and `STATUS`. `LENGTH=55h+payload_count`; sum of every complete packet byte, including checksum, must be 0 modulo 256. Big-endian 16-bit data. `SEQ=01..FF`, only one pending transaction.

**Phase 1:** `INFO (01)`, `READ (10)`, `GATHER (11)`, `CLOSE (7F)`. `INFO` accepts a selector; `READ` requires `addr16, count8`, 1–16 bytes; `GATHER` accepts 1–8 `addr16,width8` descriptors where width is 1 or 2, and validates all before any sampling. Reply payload cannot exceed 34 bytes. `CLOSE` resets only developer state.

**Phase 2:** `SNAPSHOT (12)`, `TRACE_CTRL (20)`, `TRACE_FETCH (21)` after independent timing/RAM clearance. Four 6-byte trace events plus header/meta fit in a maximum 34-byte response. A trace record means a known instrumented point fired, **not** instruction-level single-step.

A host may send multiple complete frames in a single socket write, but the protocol remains **stop-and-wait**: one outstanding request, no unacknowledged command stream. Android's compiler batches compatible reads inside `GATHER`. For busy/overrun, avoid overwriting a pending request or reply; if unable to return BUSY safely while transmitting, discard and let the host timeout/retry **idempotent read requests only**.

## Milestones (each independently reviewable PR)

### M0 — pin baseline and build harness (no target patch)

- Create `patches/`, `tests/`, `src/` contents as needed, starting with an image parser and exact SHA gate.
- Reconstruct input from user-provided Rev B or the archived hex; never silently substitute stock $31 or Rev A.
- Record `ROM parent SHA`, all target byte edits, expected original bytes, injected assembly map, checksum algorithm and rollback patch. A wrong parent SHA or unexpected original byte is a fatal build error.
- Regression fixtures: reset, crank, idle, normal scheduler, fuel, spark, IAC and ordinary `$F4` ALDL with deterministic baseline observations.
- **Exit:** baseline reconstruction hash and existing tests agree; no changes to engine BIN.

### M1 — memory, timing, descriptor and bridge audits (no target patch)

- Exhaustively classify remaining `$F5` descriptor chains, receive destinations, transmit origins, session ages, `$0399` consumers, `$3FFC` output-latch effects and any external communication trigger.
- Certify a ROM code cave by checking direct/indirect branches, table pointers, runtime page/pointer creation and calibration/patch conflicts; fail closed on unresolved owners.
- Certify RAM (RX, reply, status, stack margins) using indexed-owner tracing, reset clears, frame/stack simulation, and stress scenarios. Explicit byte-by-byte `ram_allocations.json`; avoid `$03B0–$03FF`.
- Measure dispatch frequency and **worst-case** slot A service and SCI RX/TX ISR budget under relevant simulated/bench conditions. Establish the allowed cycle bound; no fabricated time allowance.
- Determine whether RX payload memory can be reused as reply storage; if no safe lockout, allocate a separate audited TX payload region rather than force reuse.
- Verify existing adapter PCM-side SCI speed and echo/bus turnaround (Bluetooth UART is still 9600 8N1).
- **Exit:** approved allocation and hook manifests, no unresolved injection overlaps or required side effects, and initial WCET budget.

### M2 — first end-to-end image: `INFO` + `CLOSE`

- Add minimal hook for `$F5` identification and **staged** incoming payload; original `$F4` byte paths remain untouched.
- Validate complete frame **before** changing command state. Reject malformed length, framing/SCI error, bad checksum and stale partial frames with no engine-state stores.
- Lock one command buffer, atomically publish `PENDING`, and service exactly one operation from slot A at `$7B39`. Preserve RTS, caller registers/flags per verified ABI.
- Return a compact `INFO(selector 0)` with explicit protocol major, *build-generated identity token*, capabilities and payload limit. Do not compute SHA-256 on HC11. `CLOSE` acknowledges and cleans up.
- Route developer replies through existing SCI transmit and checksum path without the OEM `$F5` descriptor/destination side effects. TX complete alone releases buffer ownership. Define exact behavior for echo, RX during TX, aborts and timeout.
- **Exit:** host-generated reference frames round-trip in ROM simulator/serial bench fixture; `$F4` and engine-output differential tests pass. Still not a truck-tested BIN.

### M3 — bounded `READ`

- Add ROM/RAM allowlist *in firmware* with 16-bit overflow/cross-boundary checks; exclude direct HC11/ASIC registers and all read-to-clear/unknown I/O.
- Copy at most 16 bytes to the sealed reply. Handle ISR-mutated words with independently verified atomicity/double-read rules and label noncoherent results.
- Reject every invalid address, count, width and privilege state with zero unintended reads/side effects.
- **Exit:** compare against independent expected ROM/RAM fixtures, boundary checks, mutation-under-read and corrupted-frame fuzzing.

### M4 — `GATHER` and protocol freeze

- Parse up to 8 descriptors, prevalidate the complete set and total response width, then perform only allowed reads.
- Never claim cross-variable control-cycle coherence. Do not globally mask interrupts for a whole gather; use brief proved-safe word sampling if required.
- Regression at worst-case request/reply sizes (up to 37 bytes on wire each), including back-to-back requests, timeout/reconnect and maximum engine/serial load.
- Freeze `protocol v1` for Android implementation and emit build-specific identity/allowlist manifest. Define capability bits so an app cannot send unsupported Phase 2 requests.
- **Exit:** all Phase 1 commands verified in simulator **and** physical bench with no timing regressions. Generate the first identifiable **Dev-Enabled OS BIN/XDF pair** only after this gate; do not overwrite Rev B.

### M5 — release discipline and measured integration

- Produce `releases/<version>/`: matching BIN, XDF, parent/target SHA, before/after byte ledger, checksum record, optional address-register changes, simulator/bench test reports, known limits and rollback.
- Run original Rev B reset/idle/fuel/spark/IAC/ALDL fixtures against both parent and dev variants and compare time-critical outputs and event times, not only final values.
- Verify worst-case RX/TX interrupt latency, watchdog resets, disabled/idle developer mode and disconnection recovery. No road/vehicle validation is asserted until recorded separately.
- **Exit:** versioned, reproducible, bench-verified *read-only* release candidate, not silently promoted to vehicle-tested.

### M6 — snapshot publications (separate firmware feature)

- Pick 2–3 exact producer-boundary hook sites in fuel/spark/idle. Copy a tiny fixed group into separately owned RAM with publication sequence to prevent partial reads.
- Publish group layout/version in Android manifest, add `SNAPSHOT` and tests for ISR interleavings, skipped cycles and age/stale markers.
- **Exit:** captures are coherent at the **documented boundary**, and measured hook cost is within budget.

### M7 — trace ring (separate firmware feature)

- Prove *additional* RAM; no trace ring without an approved allocation. Start with a few event IDs (mode transitions, idle state, selected fuel/spark completion).
- Constant-time record insertion with an explicit overwrite/loss policy; host fetch is paginated, request/reply only. No bytes sent from engine/reference IRQ.
- **Exit:** loss counts, tick source/rollover, latency and highest-load stress proven.

### M8 — optional temporary experimental overrides (not authorized by this plan)

Only after separate review: typed allowlisted variables, compare-old-value, range limits, permitted engine-state checks, bounded TTL, and exact rollback on close, reset, timeout and disconnect. No unrestricted memory/register writes, runtime machine-code execution, or ROM programming.

## Validation matrix

| Case | Must prove |
| --- | --- |
| Bad length/checksum/magic/version | No command executed; no fuel/spark/IAC/state alteration |
| Partial frame, abort, SCI error, unsolicited bytes | Receiver returns to IDLE, storage bounds honored |
| Busy while TX, echo and duplicate request | Existing sealed reply cannot be corrupted; retries only for safe reads |
| ROM ends / RAM holes / I/O addresses / width overflow | Rejected by PCM, not merely by Android |
| Engine + serial concurrency | No missed injection/ignition events, no watchdog starvation, no changed IAC phase command |
| $F4 OEM scanner after developer close | Original engine diagnostic responses preserved |
| F5/session aging and shared $3FFC | No unintended output-latch bit changes or bus-drive lockup |
| Reset and failure recovery | No lingering flags/interrupt masks; baseline control starts normally |
| Binary release + matching XDF | Exact hashes, checksum, deterministic build, safe rollback |

Tests should run in CI where possible, using the existing `hac31_romsim` and repository's factory/manual-idle verification suites. Add SCI/device stimuli and time accounting to the simulator if they are missing. Simulator success proves software behavior; a powered bench PCM still must establish physical timing.

## First actual engineering change

**M0 + M1 PR:** `firmware/patches/` baseline verifier, `firmware/tests/` baseline/serial fixtures, `firmware/docs/ROM_RAM_ALLOCATION_AUDIT.md`, approved address-map/patch manifests and measured entrypoint/timing assumptions. **Do not patch `$F90B` until this audit closes.**

**Next separate PR (M2):** minimal `$F5` receive -> `INFO/CLOSE` -> TX round trip; do not introduce READ/GATHER at the same time. Advance only after all parent-versus-dev regression and malformed-frame tests pass.

These milestones do **not** close the repo's independent TS00 Rev B on-truck calibration validation gate.
