# Controller boot contract

The stock BMHM image remains the byte authority (SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`).
The callable controller stage begins at **7393**, after the final retained-boot
STAB instruction at7391. It ends before the next stage at7431.

| C entry | Stock entry | Scope |
|---|---|---|
| `pcm_reset_controllers` |7393..7430|Connected MAP/BARO, coolant/environment/spark, IAC, oxygen, TPS, EGR and board/timer seeds.|
| `pcm_baro_seed` |C614..C667|Retained/default BARO and four interpolated outputs; no MAP acquisition.|
| `pcm_iac_boot` |925E..92A3|Lost-memory cell seeding, shutdown choice, kicker qualification and output enable.|
| `pcm_iac_restore` |92F1..93C4|Warm snapshot growth and high-byte learned-cell restoration.|
| `pcm_iac_step_disable` |93C5..93CF|Retain coil ring unless a reset is already active.|
| `pcm_transmission_throttle` |B0E4..B1AB|Diagnostic qualification, zero learning, history copies, filtered TPS and kickdown.|
| `pcm_egr_feedback` |D14E..D1F5|Position ADC, zero tracking, lag filtering and reference adjustment.|
| `pcm_controller_baselines` |74D3..74E9|D000/DFFF board commands, separate11-cycle delays and initial gear.|

The reset wrapper calls the existing real coolant, environment, spark auxiliary,
TPS-zero, IAC-cell seed and kicker-disable bodies. It does not route these
through fake-success task callbacks. The old `PCM_RESET_CONTROLLERS` and
`PCM_EGR_FEEDBACK` enum slots remain reserved for source compatibility.

The initial MAP conversion subtracts26 with byte wrap before multiplication.
The old coolant sample is captured across the three conversion calls for the
hot-restart comparison. Oxygen1/oxygen2, MAP and TPS filter seeds write only
their specified high bytes; existing low fractions survive. The transmission
temperature seed at01A2 is a full word with zero fraction.

IAC warm growth clears an integral fraction only when its exact word store
runs. Overflow while constructing the first AC value in either bank also
writesFF to that integral's low byte; snapshot overflow does not. Instruction
9343 is **BITA RAM0008**, so the actual old IAC target participates. Replacing
it with an immediate08 option test changes the factory behavior.

TPS history copies01A8→01A9 and01A6→01A7 are overlapping word operations,
performed in that order. The latter captured high byte supplies the lag8
target. Zero-offset increments wrap before the unsigned minimum cap. The
published adjustment at00B2 follows signed overflow saturation and kickdown
uses its previous-state threshold before clearing/requalifying the bit.

EGR conversion retains the literal SEI/CLI window and consumes ADR4 even
after timeout. Its zero minimum/maximum reads remain separate where the ROM
rereads them. The final +0080 is a wrapped word addition, not a saturating
round operation. F436 coefficients retain all two/three provider reads;
F4C1 retains the initial adjacent-knot word and the later base-knot byte read.

All logical RAM operations require a provider bound to canonical Pcm owners.
This is the same contract used by ALDL and retained boot. The fixture binds
the involved native fields explicitly; it does not prescribe native struct
placement. Named stage data not yet consumed by another native routine remains
in the external logical address-space contract. No target ROM is generated.

Focused verification passes **2,773 C/ROM comparisons**, covering **all365 new
scoped instruction starts**. Cases cover joined controller calls, loss/shutdown
branches, retained fractions, coefficient/port/coordinate mutation, saturation,
ADC timeout and324 selected failed-prefix cases. Every provider operation on
the representative paths is failed separately. Kernel and hardware smoke
contracts also pass with the controller task boundary removed.

Transactions compare logical operand access/width/order and literal IRQ-mask
assignments. Private HC11 stack traffic is excluded. Existing native callees
contribute actual resulting state; their field accesses are not fabricated as
provider events. Shared math helper stack accesses are excluded, while live
ROM coefficient and curve reads remain visible. This is not physical bus,
target ABI, interrupt-interleaving or device timing validation. Full repository
regression remains deferred until the requested "pull and merge" step.
