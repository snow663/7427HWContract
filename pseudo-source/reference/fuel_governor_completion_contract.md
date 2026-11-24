# BMHM governor target completion — $8F5F..$90D2

## Scope

The previously explicit $8F5F..$90D2 controller dependency is now a set
of five callable public C routines, with one private header containing
68HC11 lookup/multiply helpers:

| Stock scope | C entry | Purpose |
| --- | --- | --- |
| $8F5F..$8FCB | `pcm_fuel_governor_rate` | F499 capped table, F550 rounded 8×16, three saturating rate terms |
| $8FCC..$900F | `pcm_fuel_governor_ordinary` | Subtract/add $028A/$0290; preserve the first $0286 store and distinguish $9093 from $9097 |
| $9010..$9096 | `pcm_fuel_governor_lead` | Signed $028D acceleration branch; $50EE lead-RPM and $50FA temperature lookup; $0286 publication |
| $9097..$90D2 | `pcm_fuel_governor_finish` | $0292 auxiliary clamp, publish $0299, conditional $0075.0/.1/.4 release |
| $8F5F..$90D2 | `pcm_fuel_governor_compute` | Branch-complete ordinary/lead composition, one common final stage |

The $8F3B..$8F5C mode selector returns the factory $0075&$81 test as
a boolean. `pcm_fuel_governor_target` now connects the resident RPM
error and VSS/TP input stages to that selector and the full calculation.
`PCM_GOVERNOR_TARGET` is a reserved legacy task index, no longer called.

**The optional $1809 heads-up module remains a real dependency.**
If enabled by $0086.6, the source calls that module between $8EDA and
$8EE4. The module must return A and CCR carry: carry set publishes A to
$0299 and exits. A module returning carry clear continues into VSS,
TPS-mode and the new ordinary/lead computation. Until its target ABI is
defined, absence explicitly yields `PCM_UNIMPLEMENTED`.

## Critical arithmetic/ordering properties

- F499 ($50E8) caps input and, **only if above the cap**, rereads its
  first table byte before F4BD. The four-phase interpolation reads
  two adjacent knots as one big-endian word and rereads the first
  knot after the multiplication (important for mutable test providers).
- F550 multiplies an 8-bit gain by a 16-bit intermediate using a
  separately rounded low-byte partial. Replacing it with ordinary
  truncating 16×8 multiplication is not equivalent.
- The three ASLD rate series saturate at $FFFF on carry; the $0292
  auxiliary field is the high byte of the last saturated result.
- Ordinary-mode subtract stores $0286 **after** the first subtraction
  when it is in range, before subtracting $0290. The second result
  normally supplies only the candidate high byte at $9097. A first
  underflow/minimum exception instead reaches $9093 and **stores**
  the clamped whole $0286 word with low byte zero.
- Lead-mode signed $028D is tested as signed for BLT, but the chosen
  multiply uses its original *unsigned* byte. Overflow of
  $0286 + gain×error saturates to $FF00, not $FFFF.
- Common post-correction tests $0075&$84 first, then uses the saved B
  byte snapshot for the later $11 gate. The final $50D9 comparison
  executes only if the prior flags require it and the integral high
  byte $0288 is zero.
- Existing RAM ownership is reused for $0286, $0288, $028D, $028E,
  $0293, $0294 and $0299. New named fields represent $028A, $0290,
  $0292. Calibration reads are through physical logical-address
  callbacks rather than reconstructed hardcoded constants.

## Verification status

`fuel_governor_compute_contracts` is registered in both the CMake
fast gate and `tests/run_checks.py`. Directed cases cover the
F499 cap reread, ordered table reads, F550 partial rounding, ordinary
add/sub and retained-first-store cases, lead-branch selection,
negative derivative, $0288 cleanup, and failures after partial work.
The earlier individual governor test fixtures remain registered.

A dedicated `fuel_governor_rom_differential` harness is now registered.
It replays source-evidence BMHM bytes on the repository's HC11 core and
compares 8 governor entry modes with C native-state publication, using
recorded ROM calibration, directed edge cases and randomized histories.
It deliberately excludes the unresolved optional $1809 ABI and labels
its sparse recorded-ROM view as nonflashable.

The branch-specific GitHub Actions run
[44744985921](https://github.com/snow663/7427HWContract/actions/runs/44744985921)
passed all 43 quick contracts and the focused governor C/ROM replay,
covering normal/lead/actuator paths across directed and random BMHM
state/calibration histories. This is bounded source parity rather than
a full target ABI, $1809 or connected fuel-cycle proof. The fast dispatcher still delegates the broad
`PCM_FUEL_CONTROL` routine until provider aliases, complete
$7D4B..$8547 cycles, and emitted injector safety boundaries are
tested. The code remains nonflashable source, not a PCM BIN.
