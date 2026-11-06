# Rev B developer-console integration ledger

## Reference source

- Parent candidate: `0.3.12_engine_only_manual_idle_revB.bin`; SHA-256 `e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1`.
- Primary design: [RevB_ALDL_Developer_Console_Design_v0.2.md](RevB_ALDL_Developer_Console_Design_v0.2.md).
- Source evidence: `7427_RevB_Operation_By_Operation (1).zip` (user-supplied); do not treat older HAC annotations as proof of Rev B semantics.
- Existing repository contracts: `docs/investigations/MANUAL_IDLE_REVB_RELEASE.md`, `maps/maintenance/` and `AGENTS.md`.

## Technical assumptions awaiting closure

| Target | Purpose | Current disposition |
| --- | --- | --- |
| $F5 | Retired transmission ALDL service | Proposed takeover; audit retained descriptors/side effects |
| $F927 / $F90B | Descriptor selection and SCI RX | Early routing / staged payload after full checksum |
| $F96B / $F9BE | OEM payload write/accept | Bypass write-through for developer messages |
| $F822 / $FA28 | OEM TX driver/response | Preserve low-level driver; adapt reply buffer |
| $7B39 / $7B3D | Retired scheduled entries | Candidate service calls; verify slot timing/ownership |
| $036C–$038D | Existing 34-byte receive staging | Candidate reused as bounded single-command buffer |
| $039A–$03AF | Candidate small state | **Not allocated**; indirect RAM ownership audit pending |
| $AE85–$C56E | Candidate FF-heavy ROM | **Not allocated**; indirect/jump-table/patch audit pending |
| $3FFC | Shared output latch | Preserve existing driver-enable and unrelated hardware bits |

A byte value of `FF` does **not** itself prove free code space: `FF` is a valid HC11 opcode.

## Execution model

Android command syntax -> image-specific symbol/type resolution -> grouped binary opcode(s) -> stop-and-wait framing -> validated PCM queue -> bounded background service -> prepared binary reply -> Android decode/format/export.

Mainline execution may return BUSY; SCI interrupts must only accept/discharge serial bytes and **must never** parse scripts, block, print formatted text, or perform long control operations.

## Acceptance checkpoints

**P0 / wire spec:** Host vectors round-trip; bad length/checksum rejected.  
**P1 / read-only PCM:** $F5 staged INFO, READ, GATHER and CLOSE; $F4 remains unchanged; no writes from malformed requests.  
**P2 / Android:** Connect to existing paired SPP transport; script compiler + hex/typed results; correct build manifest.  
**P3 / instrumentation:** Coherent named snapshots, bounded trace buffer and WCET measurements.  
**P4 / experimental:** If authorized, time-limited allowlisted overrides with rollback and engine-state gating.

Every changed BIN requires an exact SHA-256, parent identity, diff/patch manifest, ROM checksum validation, emulator tests and a matching XDF. Record physical verification separately.
