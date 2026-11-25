# Native artifact and bus boundary regressions

Baseline: development `f2f493f4df5843d37baf23d27a460dbd7d890476`.
These development-only files are absent from pinned main `56a3145`.

## Confirmed: an aperture can cross the EEPROM classification

`pseudo-source/platform/hc11_bus.c:103-122` originally checked only the
resource classes at the first and last addresses. Both `$0400` and `$1FFF`
classify as `PCM_HC11_EXTERNAL_GEN`, but `$0E00..$0FFF` between them classify
as `PCM_HC11_CONDITIONAL_EEPROM`. A single `$0400..$1FFF` read window was
accepted, and the region lookup granted reads throughout it.

The compiled-C test in `tests/audit/test_artifact_integrity.py` demonstrates
the invalid binding and checks that three explicitly separated valid windows
remain usable. The correction limits each binding to one contiguous resource
interval. The existing write authorization callback was still called for
non-internal writes; this finding does **not** establish an authorization bypass.

**Severity: high for a native hardware adapter.** This invalidates the claim
that accepted windows necessarily respect the resource boundary. It does not
demonstrate that a particular deployed table used the invalid spanning window.

## Confirmed: missing vector entry bytes were accepted

`pseudo-source/native/compose_hc11_rom.py:87-100` originally validated vector
values and address ranges without requiring bytes at either the reset or trap
entry. Removing the fixture's `$7110` reset segment or `$7120` trap segment
still produced an image; the absent bytes became `$FF` padding. The report
nevertheless described all non-reset vectors as an engine-off safe trap.

The correction requires both entry addresses to be present and makes the report
precise about what is verified. Presence is only a necessary condition: arbitrary
bytes at an entry do not prove a complete or safe handler. No handler behavior is
claimed, and `flash_ready` remains false. Each absent entry has a regression.

**Severity: high for image acceptance.** Previously accepted composed images
need their supplied handler bytes rechecked; a successful composition was not
evidence that the reported handlers existed or behaved safely.

## Confirmed: the ELF report was not bound to the supplied code

`pseudo-source/native/compose_hc11_linked_boot.py:40-47,77-104` trusted an
inspection schema/provenance and matching entry addresses. It did not bind
the S19 bytes or nm listing to that report. The build driver recorded the ELF
hash before exporting S19, without a code/symbol/report bundle identity.

Minimal cases that were accepted: change the synthetic C entry byte from RTS
to NOP while keeping the old report; append a symbol to the nm listing; or move
the reported BSS range from `$0600..$063F` to `$0700..$073F` while preserving
its length and capacity. These are acceptance failures, not evidence that the
repository's actual artifacts had been mixed.

The build driver now binds canonical `(address,value)` C code, exact nm text,
and all inspection metadata (including the ELF hash) after objcopy succeeds.
The boot composer requires a matching bundle. Synthetic native tests carry
explicitly synthetic bindings. This prevents accidental stale/mixed artifacts;
it is **not** cryptographic authentication or a substitute for inspecting a real
ELF from a trusted build. ASM11 listing offsets and source authority still need
independent validation; a non-empty authority string alone is not evidence.

**Severity: high for equivalence provenance.** Native image composition cannot
establish that the accepted machine code is the implementation whose ELF layout
was inspected without this or an equivalent artifact binding.

## Reproduce before and after

Run these tests from the audit checkout; `AUDIT_REPO` selects the code under test:

```sh
AUDIT_REPO=/path/to/pinned-development \
  python3 -m unittest discover -s tests/audit -p test_artifact_integrity.py -v
# Baseline: 8 tests, 7 failures, 1 passing valid-bundle control.

python3 -m unittest discover -s tests/audit -p test_artifact_integrity.py -v
# Audit correction: 8 tests pass.

python3 -m unittest discover -s pseudo-source/native/tests -v
# Existing native contract suite: 32 tests pass after fixture bindings update.
```

All native code in these regressions is synthetic and does not execute a real
reconstructed C firmware BIN. The existing host bus contracts are an additional
compatibility check; they do not qualify the physical board's EEPROM behavior.
