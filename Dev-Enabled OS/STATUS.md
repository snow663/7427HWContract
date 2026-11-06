# Dev-Enabled OS — active status

**2026-11-06.** Repository workstream bootstrapped. Phase 0: source-backed integration design and host protocol fixture.

## Completed

- [x] Separate root directory and explicit ownership boundaries.
- [x] Preserve Rev B parent identity and existing firmware/release work.
- [x] Import v0.2 design, Python binary frame reference, and deterministic test vectors.
- [x] Define firmware, protocol, Android and documentation locations.

## Next gates (not yet complete)

- [ ] Audit every remaining $F5 descriptor, RX/TX owner, and $0399 side effect.
- [ ] Prove ROM/RAM allocations, indexed/pointer uses, stack watermark, and scheduler timing.
- [ ] Prove physical PCM serial bitrate and $F5 bus behavior through the existing adapter.
- [ ] Implement read-only $F5 RX staging, deferred INFO, and safe TX response.
- [ ] Verify invalid frames have no effects; verify ordinary $F4 behavior remains identical.
- [ ] Implement READ and GATHER with address-allowlist and ISR coherence checks.
- [ ] Create a build reproducible **dev-enabled BIN + matching XDF** from exact Rev B parent.
- [ ] Validate target image in ROM simulator and bench timing before any on-engine test.
- [ ] Build Android APK, connect 9600 8N1 bridge, and verify command compiler against PCM.
- [ ] Add TRACE/SNAPSHOT and approved temporary test operations only after read-only milestone.

## Boundary

This directory is **not** a claim that custom console firmware is flashed or ready for road testing.
Work under `firmware/` and `android-app/` must keep clear **proposed / source / simulator-verified / bench-verified / vehicle-verified** statuses.
