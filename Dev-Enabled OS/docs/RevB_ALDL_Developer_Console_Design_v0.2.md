# Rev B ALDL Developer Console — Firmware Integration and Minimal Binary API

**Revision:** 0.2 — design/audit, not a firmware patch  
**Basis:** `7427_RevB_Operation_By_Operation (1).zip`, image SHA-256 `e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`; companion `RevB_ALDL_Developer_Console_Design_v0.1.md`.  
**Transport:** Existing working Android → Bluetooth serial → ALDL arrangement; Bluetooth-side UART **9600 8N1**. Preserve proven interface and PCM SCI configuration; don't introduce a second serial compatibility layer.  
**Scope:** Define a feasible firmware interface and Android-side command compiler. **No BIN, firmware, XDF, ROM, or Android app modified.**

## 1. Decision and boundaries

**Architecture:** Android parses a rich command language, resolves a build-specific symbol manifest, compiles fixed binary operations, sequences/polls/branches on responses, and formats all results. The HC11 PCM runs a small binary dispatcher in its *existing* scheduled background time. The PCM does **not** parse text, maintain a general symbol dictionary, execute scripts, perform arbitrary code jumps, or send formatted console text.

**Use the existing `$F5` message identifier as an exclusive developer channel.** Retired transmission behavior is not needed. Conventional `$F4` engine diagnostics can remain accessible when the developer console is closed; the host does not operate both sessions at once. There is **no added OEM Mode `$0B`**: the original `$F96E/$F972` mode selector rejects modes above `$0A`, and retaining an extra OEM mode adds little value when taking over the complete `$F5` command namespace.

**Important qualification:** The entire `$F5` transmit/receive **descriptor behavior** cannot simply be left untouched. The retained `$F5` receiver selects write destinations, and OEM reply construction depends on `$0399` and the descriptor. The takeover requires a developer-specific receive-buffer branch, a deferred command-execution path, and a prepared-response TX path. Neither a descriptor relabel nor a change to one command byte is sufficient.

**No persistent/on-road control writes in initial release.** Phase 1 read-only. Phase 2 non-invasive instrumentation. Phase 3 selectively authorized RAM overrides only after full state and rollback testing. This keeps engine time-critical timing independent of console activity.

## 2. Source-level findings in the supplied *Rev B*, not just factory HAC

| Image anchor | Verified code behavior | Required integration |
|---|---|---|
| `$FFD6 → $F7EA` | SCI vector reaches retained receive-first IRQ arbitration. | Preserve IRQ and electrical release. |
| `$F90B` | Reads SCI status/data; maintains checksum and RX age. | Reuse byte acquisition and checksum; route developer bytes to staging. |
| `$F927`, `$51BF` | Normal descriptor search; linked `$F4` descriptor followed by `$F5` at `$53A8`, which links to `$53C9`. | Detect `$F5` and transfer control to developer framing; retain `$F4` path. |
| `$F955–$F963` | Length byte is `0x55 + N`, accepted `N ≤ 0x22` (34 bytes). | Keep same ceiling and checks, reject too-short developer payloads. |
| `$F96E/$F972` | OEM command-mode byte is limited to `0x0A`. | Bypass OEM mode decoder only for developer `$F5`. |
| `$F9AB/$F9AE` | Original path immediately writes payload bytes through descriptor-selected pointer. | Developer input **must never** use the OEM destination write path. Stage first, apply only after checksum validation. |
| `$F9B9/$F9BC` | End-of-frame checksum verification before acceptance. | Mark pending developer request only for valid length/checksum/version. |
| `$F9BE–$FA24` | OEM acceptance changes session command/state, including `$0399` when ID is `$F5`. | Bypass *these* `$F5` side effects and factory immediate-reply handling. |
| `$FA28` | Begins transmit, enabling driver via `$3FFC`. | Reuse TX start semantics for prepared binary responses. |
| `$F822`, `$F8E6`, `$F8F4` | Descriptor-based byte selection; common SCI byte send/checksum and completion. | Add fixed-size developer reply-buffer selector, reuse send/completion. |
| `$F781` | Session expiry can clear `$0399`, `$038E`, flags and driver. | Keep normal expiry/driver behavior; add distinct developer pending/busy/session cleanup. |
| `$F5E8` | Scheduled broadcast service uses phase-indexed table at `$518F`. Image table bytes `$518F–$51AE` are all zero. | No active scheduled descriptor found *in this particular table*; still verify every possible TX trigger. |
| Slot A, `$7B39–$7B3C` | Three NOPs, RTS; dispatcher pointer `$7A99`. | Patch with `JSR DevService`, keep `RTS`. |
| Slot B, `$7B3D–$7B43` | Six NOPs, RTS; dispatcher pointer `$7A9B`. | Optional second bounded service/trace-maintenance call. |

The background service must not run synchronously in `$F7EA`. The dispatcher decides when slot A/B executes; **their real admission frequency and worst-case runtime are not measured** by a static image. Slot B may be unnecessary for Phase 1. Other engine work in the same schedule keeps its existing slot positions.

## 3. ROM and RAM budget — evidence versus proposed reservation

**ROM candidate:** `$AE85–$C56E` inclusive is **5,866 contiguous `FF` bytes** in the exact reconstructed image, classified as non-rooted FF-valued bytes by its ledger. Attractive for new executable code, with ample nearby space for a short initial command handler. **Not yet certified free**: prove no pointers, indirect accesses, jump-table uses, calibration use, runtime-created execution entries, and patch relocation conflicts. `FF` is also a valid HC11 opcode; do not infer free space solely from the fill value. Another candidate `$5CDD–$70FF` is 5,155 FF bytes, but overlaps the legacy calibration-address region and is a poorer default if future calibration expansion is planned.

**RAM Phase 1 candidate:** Existing ALDL receive window `$036C–$038D` = **34 bytes**. Stage a developer request there, then after successful validation and command extraction, recycle the same window for one prepared response payload (single transaction at a time). It must remain immutable until TX completion. An incoming second request while pending/transmitting is rejected or discarded, never allowed to overwrite the prepared reply.

**Small-state candidate:** `$039A–$03AF` = **22 bytes** is not directly referenced by any instruction in `OPERATIONS.csv`; a raw 16-bit ROM-immediate/pointer scan also did not establish a reference into it. However the static analysis cannot rule out indexed/callee access, pointers built in RAM, or boot-time RAM procedures. Startup explicitly clears `$0360–$03FE`; that is compatible with zero-initialized state but **not ownership proof**. `$03B0–$03FF` belongs to the stack/stack-watermark area and must not be borrowed. Do not claim `$038E–$0399` as free: engine command/diagnostic data at `$038E–$0398` is still referenced outside serial; only the `$0399` retired transmission-command role is substantially reclaimable after all surviving serial use is disentangled.

**Estimated incremental state (not allocated):** one pending/busy/status byte, session/sequence bytes, RX/TX operation counters, output length/index, 16-bit scratch pointer, error counters, and watchdog/timeout state; target **16–22 bytes**, subject to a byte-exact memory allocation and access-owner audit. Additional 96–192 bytes for a trace ring are **not** presumed free and must be separately sourced before Phase 2.

**Capacity:** Existing receiver permits 34 payload bytes. With ID+length+checksum, a maximal frame is 37 bytes. At 9600 8N1 a 37-byte one-way frame occupies about 38.5 ms on the Bluetooth UART; a maximum-sized request plus maximum-sized response needs at least ~77 ms of serialized link time, before PCM scheduling/turnaround. This is a limit, not a target polling rate.

## 4. Binary protocol — v1 exact proposal

### Envelope

```
Request:  F5 LEN D6 01 SEQ CMD [ARGS...] CK
Response: F5 LEN D6 01 SEQ (CMD|80) STATUS [RESULT...] CK

LEN = 55h + N, where N is the count of bytes from D6 through last argument/result
CK  = (-(F5 + LEN + sum(payload))) & FFh
Validity: sum(all frame bytes) & FFh == 00h
```

Requests: `4 ≤ N ≤ 34`; replies: `5 ≤ N ≤ 34`. Binary integer addresses, cursors, counters, and values are big-endian. `SEQ` runs `01..FF` with `00` reserved; the host does not have multiple outstanding requests. Replies have the same `SEQ`; request opcodes `00..7F`, response opcode is ORed with `80h`. Distinguish physical-adapter TX echo from replies by opcode direction and matching transaction ID. No unsolicited frames in v1.

On checksum/length corruption: discard without applying any command or reply (when sequence validity cannot be trusted). On a **valid** request with bad argument count, version, address, or state: return an explicit error. Do not reuse a previous request's trailing bytes. Duplicate state-changing transactions (Phase 3) require a cached sequence/result or stronger nonce/session checking. A read command may be retried by Android; a non-idempotent command may not be blindly retried.

### Deliberately small PCM instruction set

| Opcode | Primitive | Request arguments | Result | Release |
|---|---|---|---|---|
| `01` | `INFO` | `selector8` | `selector8` + fixed compact record: build token/capabilities/protocol, status/counters, or selected identity | 1 |
| `10` | `READ` | `address16, length8` | `address16, length8, bytes[1..16]` | 1 |
| `11` | `GATHER` | `count8, (address16,width8)×count` | `count8, concatenated raw values in request order` | 1 |
| `12` | `SNAPSHOT` | `group_id8` | Group ID, capture sequence/tick and compact prepublished raw image | 2 |
| `20` | `TRACE_CTRL` | `action8, mask16` | State, mask, ring capacity, overrun state | 2 |
| `21` | `TRACE_FETCH` | `cursor16, count8` | `next_cursor16, overrun16, records[]` | 2 |
| `7F` | `CLOSE` | none | Closed/cleared developer session | 1 |

**Phase 1 implements just four opcodes (`01`, `10`, `11`, `7F`)**. `SNAPSHOT`, `TRACE_CTRL`, `TRACE_FETCH` are designed now but absent until the RAM/timing audit. Reuse `INFO` selectors rather than adding separate `HELLO`, `PING`, `READ_COUNTERS`, and firmware-fingerprint opcodes. Android `help`, `watch`, `diff`, `search`, `plot`, `export`, `when`, and `repeat` are **host commands** and consume no new PCM opcodes.

`READ`: only audited RAM and ROM regions; no unrestricted reads of `$3000–$303F` HC11 registers, `$3F00–$3FFF` ASIC/board I/O, external strobes, stack/unknown address spaces, or write-sensitive registers. ROM address range `$4000–$FFFF` is a *candidate* read-only region, not proof that every address has independent CPU-side behavior. RAM ranges are enumerated by the version-specific allowlist after ownership verification; a reconstructed file's `$0000–$3FFF` padding is **not** a hardware RAM map.

`GATHER`: `1 ≤ count ≤ 8`; each width `01` or `02`, addresses validated for boundary/volatility. Maximum request payload `4 + 1 + 8×3 = 29` bytes. Maximum reply payload `5 + 1 + 8×2 = 22` bytes. This is a **bounded burst of reads, not a guaranteed same-control-cycle snapshot**. Every descriptor is validated before any data is returned, and reads cannot trigger side effects. If a 16-bit value may be concurrently changed by an ISR, arrange an audited atomic word copy or double-sample check. Do not hold interrupts masked over the complete multi-address gather.

`SNAPSHOT`: optional prepublished captures at **specific, audited engine code points** so fuel/spark/idle fields share a defined producer boundary. Merely reading adjacent addresses in a background slot does not guarantee cycle coherence. Payload group definitions are build-specific. A non-coherent group must be labeled as such by the Android manifest.

`TRACE_CTRL` actions: `00=status`, `01=arm`, `02=stop`, `03=clear`. Mask is a compact predefined event-category bitmap (not arbitrary PC addresses). `TRACE_FETCH` is host-paced; suggested Phase 2 record is `tick16 | event8 | arg0 | arg1 | flags` (6 bytes), subject to verifying an actual suitable monotonically updated tick. Reply meta `next_cursor16 | overrun16` costs 4 bytes, so at most **4 events per 34-byte response** (`5 + 4 + 4×6 = 33`). No UART output inside spark/injector/reference interrupts. Instrument only a few selected events to begin with.

`CLOSE` ends developer session, disarms trace, and rejects pending work. Version 1 is read-only and has no test values to revert; a future override module must always revert its approved temporary changes on CLOSE/expiry/reset. Session expiration policy and engine-off behavior require bench testing.

**Statuses:** `00 OK`, `01 BAD_LENGTH`, `02 BAD_VERSION`, `03 UNKNOWN_CMD`, `04 BAD_ADDRESS`, `05 ACCESS_DENIED`, `06 BUSY`, `07 INVALID_STATE`, `08 OUT_OF_RANGE`, `09 TRACE_OVERRUN`, `0A INTERNAL_ERROR`. A missing or invalid checksum cannot reliably generate a safe reply. All statuses are v1 protocol values, not inherited OEM ALDL modes.

### Example compiled requests (verified in accompanying vectors)

```
> info
  INFO selector 0 → one F5 binary request

> peek $01D9 1
  READ $01D9 ×1 → one F5 binary request

> get8 $0062; get8 $01D9; get16 $0250
  GATHER 3 descriptors → one F5 binary request (read results in same order)

> watch rpm,tps,bpw at 5Hz for 20s
  Android schedules GATHER requests and timestamps/plots results; PCM stores no loop

> if rpm > 2500 then snapshot spark
  Android evaluates condition after a response; only then transmits SNAPSHOT (Phase 2)
```

The app may concatenate *complete framed transactions* in a transport write, but with stop-and-wait operation it may not put multiple unacknowledged commands in flight. Batching is carried inside a validated `GATHER` request, not an unframed bytecode language on the PCM.

## 5. Precise firmware integration worklist

1. **Prove address ownership.** On the reconstructed image, extract references (direct/indexed/table-built), startup clears, stack watermark, all engine and retired-transmission RAM variables, and possible dynamic page/pointer paths. Reserve explicit ROM/RAM ranges with invariants and build-time overlap checks. Prioritize `$AE85–$C56E` ROM and `$039A–$03AF` small state; retain `$036C–$038D` RX/TX staging if the full indirect-use audit permits it.
2. **Minimal `$F5` RX branch.** Identify `$F5` at descriptor selection/early receive, enforce fixed 34-byte staging and `D6/01` protocol, bypass mode selector `$F96E`, bypass `$F9AB` write-through, and bypass OEM `$F9BE` transmission-mode command stores. No visible side effect until complete checksum validation. Preserve `$F4` behavior and shared SCI accounting.
3. **Queue exactly one command.** Valid frame sets a pending flag. Reject or safely ignore new requests while the buffer is owned; do not overwrite responses or turn invalid frames into changes. The dispatcher slot `$7B39` calls a small `DevService` bounded by measured worst-case cycles, and returns without waiting for serial I/O.
4. **Implement `INFO/READ/GATHER/CLOSE`.** Validate all operands before touching sources, copy reply into the shared buffer, publish a response-ready state. Use build-generated identity token matched to the Android manifest; don't compute a ROM SHA in the PCM at runtime.
5. **Dev TX selection.** Use existing $F8E6 transmit/checksum progress, `$F8F4` completion and `$F7EA`/`$3FFC` driver control. When TX is selected for a developer reply, `$F822` obtains bytes from the prepared buffer rather than ROM descriptor-controlled memory. The buffer cannot be reused until end-of-transmission.
6. **Retained service interaction.** Review `$F781`, `$F715`, `$F5E8` for `$F5` session flags, `$0399`, clear/timeout paths and old transmission replies. Remove unintended interactions *without* disabling watchdog, engine diagnostics, engine RPM/spark/fuel, or the shared output latch. `$F4` OEM engine diagnostics remain separate and are used when the dev session is closed.
7. **Instrumentation Phase 2.** Only after measuring real scheduler margins: add prepublished snapshot hooks and a bounded ring in *proven* RAM, and enable one low-rate trace category at a time. Reuse `$7B3D` if useful for maintenance; otherwise leave it as RTS.
8. **Optional Phase 3.** One new `TEST_OVERRIDE` family only for explicitly whitelisted, non-hardware variables with type/range checks, compare-and-set, finite TTL, engine-state admission, and automatic revert. No general RAM/ROM/ASIC writes, no ROM reflash via ALDL, no breakpoint halt in the running truck.

### Firmware state machine

```
IDLE / RX [receive bytes in existing SCI path]
  → validate LENGTH + checksum + header
  → PENDING (buffer locked)
  → background SLOT_A service
  → PREPARED_REPLY (same buffer repurposed)
  → TX (SCI ISR serializes bytes; no new command)
  → TX_COMPLETE (release driver; clear busy; buffer unlocked)
  → IDLE

Errors: RX reset; counters update; no write-through to engine state.
```

### Critical traps to test

- `$F5` command byte `D6` would be rejected by the current OEM `$F96E` mode logic. The new branch is mandatory.
- `$F9AB` currently stores *prior to checksum acceptance*. Do not call OEM store for developer data, even in an error path.
- `$0399` is reset/used by other serial paths, whereas `$038E–$0398` has active nonserial references. Do not treat the whole removed-transmission zone as free RAM.
- A large FF ROM run is a *candidate*, not a proof of safety.
- The `$036C` staging buffer cannot simultaneously hold an incoming command, ongoing response and unsolicited traffic.
- Slot A/B availability is structural, not an unlimited CPU-time grant. Timing needs measurement while cranking, high RPM and heavy SCI traffic.
- Arbitrary READ of a timer/ASIC register could clear a latch or alter timing; address allowlist is enforced *on the PCM* even if Android's symbol manifest is wrong.

## 6. Build-specific Android compiler and manifest

**Parser:** case-insensitive commands with identifiers, hex (`$01D9`, `0x01D9`) and decimal numbers, semicolon/newline chaining, read lists, width suffixes, `watch`, `repeat`, simple `if` on returned values, macros, and script/history files. Full type checking and address/range error reporting on Android. A macro expands into a sequence of stateless F5 requests. Conditions, timing and loops are **only** Android logic.

**Manifest:** image/build token; symbol name, address, length, signedness, scaling/unit and confidence; allowed firmware exposure; snapshot group layouts; trace-event layouts; calibration fingerprints; command capabilities. Default to raw hex if build ID mismatches rather than silently using wrong labels. A raw variable read does not prove an inherited symbol name or unit is correct.

**I/O engine:** SPP byte stream, v1 packet encoder/decoder, one outstanding request, sequence correlation, echo filtering, timeouts, RX fragmentation/corruption recovery and CSV/JSON/raw-byte exports. Polling speed adaptive to reply size, engine-response latency and error counts. Export both phone timestamps and independently sourced PCM event ticks.

## 7. Acceptance gates (must pass before engine use)

**Gate A — artifact audit:** image SHA matches; ROM insertion range passes all verified static and dynamic ownership checks; RAM state/storage avoids startup wipes after init, stack, learned state, ISR and engine state. Build-time script confirms no overlapping modified byte ranges. Original `$F4` paths and vectors preserved.

**Gate B — passive serial test:** HELLO/INFO reply and bounded READ work over existing adapter. Bad checksum, bad length, unsupported version, disconnected mid-frame, echo, stale and duplicate sequences, and RX overflow cannot change any engine variable. `READ` rejects I/O ranges. Independent physical UART capture matches generated test vectors.

**Gate C — timing test:** instrument worst-case SCI receive/TX ISR cycles and slot-A service cycles; verify no reference-event, injector output, EST, IAC or watchdog regression at low/high RPM, under maximum 37-byte traffic, including interrupted/aborted requests. No unexplained output change when the developer mode is idle.

**Gate D — instrumentation:** deliberately exercise and verify each event ID, timestamp source, loss count, ring overwrite/stop behavior, snapshot publication boundary and burst download. Event capture has fixed, measured upper-bound execution time.

**Gate E — overrides, if added:** compare-and-set failure, invalid ranges, engine-state rejection, disconnect/expiry/reset/CLOSE rollback, reconnect not auto-arming, and no side effects on forbidden outputs.

## 8. Conclusions / current status

**Implementable architecture:** yes. Rev B has a working SCI IRQ and ALDL transport, existing `$F5` infrastructure, at least one empty dispatcher slot, and a large candidate ROM region. A small read-only `INFO/READ/GATHER/CLOSE` service is a reasonable first modification. Most console sophistication stays on Android; expanding the Android syntax does not require a PCM reflash unless a genuinely new primitive is required.

**Not yet proven:** allocation safety for 22 bytes at `$039A–$03AF`; full reuse of the 34-byte ALDL RX window as a TX buffer; all indirect and runtime references to `$AE85–$C56E`; actual admitted scheduler execution time and serial timing; trace ring memory and timestamp source; compatibility of the retained TX descriptor paths with variable replies. These are explicit implementation gates, not reasons to redesign the concept.

**Recommended next actual patch:** *Phase 1a only* — `$F5` staged request, immutable 1-command buffer, `INFO(selector 0)` response, `CLOSE`, and a test harness for protocol framing/checksum/aborts. Leave read/gather until that hook demonstrably has no unintended effects. Thereafter implement `READ` and `GATHER` as a second small increment. Do not flash a console-enabled image until static/bench tests pass.