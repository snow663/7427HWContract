# Historical assembly replacement-OS prototype

This tree preserves earlier bootstrap, read-only input and debug-serial
assembly work. The active replacement-firmware source is
[pseudo-source/](../../pseudo-source/README.md).

The reported bootstrap and read-only image build proofs remain historical
proofs of those images. The serial observability stage retains its own source,
assembly and physical-verification limits. None grants production actuator
authority, target readiness for the new C source, or permission to assume
unmeasured ASIC behavior.

Keep these sources and their regression verifiers. Their ABI/layout/HAL rules
apply to this prototype. New C memory placement and interfaces are defined in
[pseudo-source/memory](../../pseudo-source/memory/MEMORY_LAYOUT.md).
Historical proof records remain under [docs/implementation](../../docs/implementation/ROM_FIRST_BUILD_PATH.md)
and [closeout](../../docs/closeout/README.md).
