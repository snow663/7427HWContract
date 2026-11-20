# BMHM governor actuator and RPM-error ports — $90D3..$9166; $8EC9..$8EDA

## Scope and authoritative source

This batch retains the stock **actuator duty-control code**, not a guessed
manual-transmission governor PID. The authority is the actual BMHM $31
instruction listing at $90D3..$9166 and $8EC9..$8EDA. The factory
calibration is a byte-addressed ROM and the board command at $306C is
a hardware **word transaction**. No physical actuator is enabled by this
host implementation or a successful C build.

The optional $400F.0 gate in the fuel prelude now calls the resident
`pcm_fuel_governor_drive`. When that bit is clear, the call is omitted.
The $8EB4 target-selection path continues to use its initial feature,
running and $006F bit-mask gates and now calls
`pcm_fuel_governor_error` before the remaining `PCM_GOVERNOR_TARGET`
boundary. The $8EDB..$90D2 calculation and $1809 extension's carry/result
semantics are **not yet implemented**. In particular, no source-less
assumption that target RPM equals throttle target is introduced.

## $90D3..$9166 actuator flow

1. Subtract actual normalized TPS $01D9 from desired governor TPS $0299.
   Use the **unsigned absolute difference** as $029A.
2. Call stock F4B6 scaled interpolation using header $50FF and its two
   live knots (first `LDD 0,X`, then reread `0,X` after the MUL). Multiply
   the returned gain by the error and twice perform ASLD; any carry
   clamps the P term at $FFFF. Store to $0295.
3. Call F4B6 at header $5109 with the same error; store the unscaled
   8x8 result in $0297 (I increment).
4. Preserve the desired-minus-actual borrow as the direction:
   desired below actual **increases** $0288 by the I term, saturating
   overflow to $FF00; desired at/above actual decreases $0288,
   flooring underflow to zero.
5. Combine the new accumulator with P: increasing direction adds P;
   decreasing direction subtracts it, flooring underflow to zero.
   Add $0080 for high-byte rounding. Saturate positive carries to
   output $FF. Clear $0288 **after** that calculation if desired=$FF.
6. If $0051.4 is set, zero the command. Otherwise, if $003B.4 is set
   and $0393.0 qualifies, replace the command with the fresh $0394
   service value.
7. Write `0x1F00 | command` to the physical **16-bit** $306C register.

The existing $0299 name remains
`PcmTransmission.governor_requested_throttle`. New canonical fields
own $029A, $0295, $0297 and $0288. The C source reads the two immutable
calibration tables through explicit logical ROM callbacks, retaining
source-access order, rather than assuming their bytes are adjacent to
native C pointer arrays.

## $8EC9..$8EDA target prelude

Clear $0075.2, then read parameter $50D8 and compare against
the **high byte of the existing RPM-monitor word $028E**. Store the
unsigned absolute difference to $0293. Set $0075.2 iff the target
was below the observed RPM coordinate. A failed $50D8 read retains
the prior completed bit clear and leaves $0293 unchanged. The next
$8EDB branch, optional $1809 module call, VSS/TPS governor flags,
integral/correction paths and $0299 update remain open.

## Verification and promotion rules

New fixtures are registered as `fuel_governor_drive_contracts` and
`fuel_governor_error_contracts`. The drive fixture contains a
262,144-case Cartesian arithmetic/accumulator sweep for four
distinct gain/accumulator profiles, independently computed expected
outputs, a mutated live table-knot reread and every selected I/O
failure prefix including service-override paths. The error fixture
contains 65,536 high-byte target/observation combinations and a
failed-ROM-read prefix. They are **defined test cases**; full
repository/CMake execution and instruction-by-instruction ROM
differentials are still pending on this branch.

The new resident governor drive is called from
`pcm_fuel_input_precalculate`, but `pcm_fuel_control` in the fast
dispatcher remains an explicit dependency. Promotion requires
$8EDB..$90D2 closure or a fully reviewed manual-only feature policy;
a canonical provider mapping for all shared runtime memory, proven
stock instruction/transaction equivalence, and joined
$7D4B..$8547 crank, run, failed-prefix and phase histories. The
target BIN and board/actuator electrical validation remain separate.
