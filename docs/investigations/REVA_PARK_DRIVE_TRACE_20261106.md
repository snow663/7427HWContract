# Rev A Park/Drive trace — 2026-11-06

The reviewed image still contains Park/Drive idle-controller alternatives and
shared Park-bank housekeeping. Its normal running selector is forced to Drive.
There is no ordinary automatic range-input selection between the two paths.
The startup base target is a separate surviving selection: it still uses the
old Drive curve, before the background target calculation uses the unified curve.

Image: `0.3.12_engine_only_spark_idle_revA.bin` (65,536 bytes), SHA-256
`d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e`.
No BIN was modified for this trace. These findings apply to that exact image.

## Selectors and admission

| Location | Rev A behavior | Consequence |
|---|---|---|
| RAM 0041.5 | Explicitly cleared by the engine-only helper and at 9185 | Legacy P/N state is held clear by resident code |
| 9188 | Jumps to 91A2, bypassing the old range decoder | The normal input service cannot set P/N from the range pins |
| 953A | Jumps directly to 954F | Bypasses both old P/N/range tests in IAC context selection |
| 954F | Sets RAM 0036.1 | Running IAC context is Drive regardless of the P/N input or range-status RAM |
| 9571..9590 | Old Park-transition body is retired | That old entry is not a callable alternative in this image |
| 4E8F.0, read at 9445/945E | Current option selects the Drive startup bank | Separate from the running forced-Drive selection; the option also participates in idle-control admission elsewhere |

The reviewed resident writers for 0036.1 are the forced-set instruction, generic
boot clearing and preserving self-copy. There is no surviving ordinary Park
selector. Arbitrary serial uploads, external code and corruption are outside
this claim. Other bits in 0036 continue to change during idle control.

Eight exact-code fixtures varied the old IAC context, P/N input and range status.
All selected Drive. A previously clear context also initialized the Drive-entry
air adder to 8 internal units, its hold to 20 calls and the qualification delay
to 80 calls. An already-Drive context did not reinitialize those terms. These
are controller units/call counts, not motor steps or seconds.

## What the remaining alternatives do

The Park comparisons below describe surviving consumer branches when entered
with an injected Park context. Normal context selection does not admit them.

| Function | Park alternative | Drive alternative selected in Rev A |
|---|---|---|
| Learned idle-air integral | 029D no A/C; 02A0 A/C | 02A7 no A/C; 02AA A/C |
| Default integral seed | 4EB1, currently 28 internal units | 4EB2, currently 38 internal units |
| Integral error gains | 4F92/4F9D underspeed/overspeed | 4FA8/4FB3 underspeed/overspeed |
| Proportional correction | 4FCC/4FD7 by error sign | 9C96 pointer family, also indexed by A/C and integral qualification |
| Stall recovery | Park entries in 504D family | Drive entries in the same family; hold at 5056 rather than 5055 |
| Conditional BLM idle-target addition | 4F8A/4F8B | 4F8C/4F8D |
| Throttle-follower decay | Fixed gain at 5070 | Drive gain family at 507C; VSS input has already been bypassed |
| Cold state/bound | 02A3/02A5 | 02AD/02AF |
| Warm learning snapshot | Park snapshot without Drive warm-valid flags | Drive snapshot sets the corresponding 0009.4/.5 flag |
| Open/unqualified learned-cell cap | No Drive-specific cap | A32A limits a Drive cell against its snapshot plus 4FC7/4FC8 |
| Cross-bank transfer work | Can propose a Drive-bank word | Can propose a Park-bank word even though ordinary Park admission is gone |

The normal base target at 98A3 uses FF60 for either injected context. It no
longer selects four Park/Drive/A/C base curves. Retained adders can still differ.
At coolant coordinate 160 with other adders neutral, both consumer fixtures
requested 850 RPM. When the low-BLM idle adder was deliberately admitted,
Park requested 900 RPM and Drive 875 RPM. This does not establish that the truck
was meeting that admission condition in any particular log sample.

The same base target also produced different stall thresholds: 51 versus 57
raw target-coordinate units in the neutral-adder fixture. These thresholds
are separate from the requested idle speed.

At error coordinate 8, no A/C, and neutral ancillary state, a single integral
call added 72/256 internal air units on the Park underspeed path versus 160/256
on Drive. Overspeed subtracted 56/256 versus 48/256. The proportional routines
also produced different terms; these are not physical IAC-step comparisons.
In a throttle-closing follower fixture starting from the same filtered word,
Park ended at 44.0 internal units versus Drive 51.5: the retained Drive path
held more follower state in that case. A throttle-opening fixture gave the
same capped result for both. Full case inputs/results are recorded below.

## Park housekeeping still affects Drive

9FDE first asks whether **either** cold-bound high byte is nonzero. It still
decays both banks. Warm snapshot admission is reached only when both bounds
have zero high bytes; it then applies the coolant, qualification and error gates.

Two otherwise identical Drive fixtures demonstrate the coupling:

| Park bound | Drive bound | Drive no-A/C snapshot | Drive warm flag |
|---:|---:|---:|---|
| 0 | 0 | Updated to 38 | Set |
| 1.0 internal unit | 0 | Retained at its seeded zero | Clear |

Thus Park state is not completely inert just because normal Park selection was
removed. It can keep the background routine on its cold route and delay a Drive
warm snapshot. This is a demonstrated code dependency, not proof that it caused
the observed warmup oscillation. Cold-bank comparison and opposite-bank transfer
work are further remnants to disentangle before excising the unused bank.

## Startup target is not yet unified

9442 starts with pointer 4F32, reads 4E8F.0 and changes the pointer to 4F50.
With the current option, 944F looks up **4F50**, then adds the startup term from
4F6E and publishes 0857 at 9470. The corresponding startup integral/cold
selection also retains the existing initialization options.

The later background calculation at 98A3 independently uses **FF60**, then
applies the retained battery, roughness, BLM, startup, slew and stall logic.
The two calculations therefore have separate base schedules. Six fixtures
confirmed the 4F50 startup selection; for example, supplied coolant coordinate
87 produced a 925-RPM startup request in this isolated fixture. The coordinate
is stated directly; this test does not independently calibrate coolant degrees.

The non-OEM read register previously marked 4F50 `omitted`. That was incorrect:
the normal background use was removed, while this startup use survives. Its row
is corrected. 4F32 remains the inactive startup alternative under the current
option. 4F41/4F5F no longer have their former named base-curve selection role;
neighboring lookup-byte overlap is a separate issue.

## Fuel and spark

The direct legacy P/N tests at 817F (DFCO qualification), 89C9 (idle AFR
admission), 8A3C (warmup AFR branch), 8CB7 (idle BLM cell offset) and E3D9
(startup AFR hold) are bypassed. The old P/N abuse branch at 8058 is also
retired. These paths no longer switch with the physical Park/Neutral input.
The common/Drive-style behavior and other admissions remain.

Rev A already forces normal base spark through 4166 and retires the alternate
428A table and separate idle/transient correction block. This trace found no
new live Park/Drive base-spark selection. Retained engine startup/coolant/knock,
deceleration and command-limit behavior remains separate from the IAC context.

The selected spreadsheet cell B365 originally names 4E72, the spark-bypass
count limit read at AC01. It is not a Park/Drive table selector.

## Verification and follow-up scope

[Machine cases](../../maps/maintenance/reva_park_drive_cases.json) record 36
bounded executions of the exact image with RAM-only fixture changes. These
compare selector admission, startup target, normal target, proportional/integral
correction, follower behavior and the shared cold-bound dependency. Interrupts
and physical I/O are not modeled by these isolated cases.

Reproduce using [the trace runner](../../tools/trace_reva_park_drive.py):

```sh
python tools/trace_reva_park_drive.py /absolute/path/to/0.3.12_engine_only_spark_idle_revA.bin
```

A future simplification should select one idle-air state bank deliberately,
unify startup with the normal base schedule, and remove cross-bank gates and
proposals while retaining the selected bank's current behavior as the comparison
baseline. Switching the current selector to Park alone would change gains,
learned cells, follower decay and recovery behavior together. No such change is
implemented or recommended as an untested replacement here.
