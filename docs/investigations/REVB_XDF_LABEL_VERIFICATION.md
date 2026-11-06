# Rev B XDF labels: instruction and execution verification

The questioned labels were retraced from the supplied Rev B bytes, including
their producers, comparisons, arithmetic and selected consumers. The previous
label review was too categorical about normalized flow units and the phrase
maximum spark retard. Both qualifications below matter.

| Evidence | SHA-256 |
|---|---|
| Actual Rev B BIN | `e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1` |
| Exact delivered Rev B XDF | `788b8f5b79c646fa072b45de5f8e075c77f5d692468d39541406676a0145214e` |
| Rev A used for the historical AE comparison | `d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e` |

[The machine-readable trace](../../maps/maintenance/revb_xdf_label_trace.json)
contains 352 decoded instruction starts, rooted direct references and the
fixture outcomes. [Recorded excerpts](../../maps/maintenance/revb_xdf_label_evidence.json)
allow CI to replay 87 Rev B instruction fixtures and 15 Rev A AE fixtures.
Synthetic calibration probes modify copied test memory only. The supplied
BINs, XDFs and calibrations remain unchanged. This is software evidence, not
a physical PCM/engine or interrupt/deadline test; TS00 truck validation stays first.

## IAC-change AE: 50A8 and 50A9 are different inputs

The current TPS producer at 7DF7 calls 5C9A. That helper rounds the learned
zero at 02F6, subtracts it from raw TPS A6 with a zero floor, applies the
normalization gain at 5B26 and saturates. It returns the normalized byte in A;
7DFA stores it in 01D9. The intermediate 01A6 store does not replace that
engine-TPS publication.

The Rev B AE slice is:

```text
9A44 STD  0871          save current pre-follower air command
9A47 SUBD 087D          subtract previous command
9A4A BCS  9A6F          negative change: zero AE
9A4C STAA 086B          save whole-unit increase
9A4F LDAA 01D9          normalized TPS
9A52 CMPA 50A9
9A55 BCC  9A6F          TPS >= threshold: zero AE
9A57 LDAA 086B          restore whole-unit air-command increase
9A5A CMPA 50A8
9A5D BCS  9A6F          increase < threshold: zero AE
9A5F ASLD               scale lookup coordinate
9A62 ASLD               saturating continuation follows
9A67 LDX  #50A2
9A6A JSR  F4B6          IAC-change enrichment lookup
9A70 STAA 087F          publish enrichment term
```

Thus 50A9 is a TPS cutoff, exclusive at equality. The delivered percent-Flow
unit describes the wrong input there. At the current raw threshold 26, TPS25
passes this gate and TPS26 does not. Percent TPS using the existing 100/256
scaling, or explicitly documented normalized counts, is appropriate.

50A8 compares the high byte of the positive Q8.8 air-command difference.
Its current raw threshold 10 admits an increase of 10 whole air units and
rejects 9, provided TPS passes. Expressing 10 as 3.90625 percent of a
256-unit normalized command scale is mathematically valid. Calling that
measured airflow percent is not established. The earlier suggestion that
percent flow must be replaced with raw units was too strong: clarify that it
is normalized **air-command change**, or intentionally choose a consistent
internal-unit display. The XDF conversion is not wrong merely because it
uses a percentage representation.

The actual Rev A bytes confirm this is not a new-controller invention:
97BD loads 01D9 before comparing 50A9 at 97C0; 97C8 subtracts the previous
087D word and 97CD compares its high byte with 50A8. All 15 old/new predicate
fixtures agree. Entering the lookup does not guarantee nonzero fuel: the
lookup calibration and later delivery accounting still apply.

## Short-pulse shaping: 4979, 4971, 496D and 496F

The normal synchronous route at 84BC loads P from 024E. The 3E.4 bypass is
separate. For the ordinary route:

1. P=0 bypasses shaping and minimum replacement.
2. For 0<P<0100, 84D6 selects table4979; F4BD clamps the input P-0020 at zero
   before the existing interpolation. 84DE adds the lookup result to P.
3. 84E1 **subtracts** the word4971. A borrow selects replacement496F.
4. Otherwise 84E9 compares the result with word496D. Below it selects496F;
   equality passes. 84F5 stores the selected pulse in024C.
5. For a nonzero pulse, the byte0256 offset is added afterward, followed by
   the existing7FFF command limit. Zero remains zero on this synchronous route.

The async helper begins at8548. Its 400E.4 option gates this same short-pulse
lookup/subtraction, and only below0100. On subtraction borrow, it selects zero
at8569 rather than the synchronous replacement. The subsequent offset/output
path is separate; do not generalize the synchronous zero/minimum handling to
every possible direct call of the async helper.

Copied-memory witnesses with table correction8 and subtraction3 turn input64
into69 in the synchronous path with the async option either clear or set.
The async path returns64 with its option clear,69 with it set. At256 neither
path shapes the input. With subtraction90, the synchronous borrow selects
replacement48 while the async borrow selects0.

To distinguish the two minimum controls, a temporary threshold32 and
replacement48 produce 0→0,31→48,32→32,33→33. A separate offset7 witness gives
selected48 followed by timer55. The actual released threshold and replacement
are both32; testing with distinct values makes their different roles visible.

The short-pulse controls therefore serve both paths, with different admission
and borrow handling. The inherited Async/CPI-only description is incomplete
for this program, and its statement that4971 is added has the wrong sign.
Suggested names: **Short-pulse added correction**, **Short-pulse subtraction**,
**Sync minimum-pulse threshold**, **Sync replacement pulse**. Raw arithmetic
is proved here; the inherited microsecond conversion is not a new measurement
of the physical injector timer or injector response.

## Desired AFR at5216 is a logging pointer

Descriptor51EF has the indirect-data format80. With its zero-based table
ordinal15, F886 doubles the ordinal, F887 advances the descriptor pointer and
F888 reads the word at descriptor+9+2*ordinal =5216. In Rev B that word is024A.
F8DC then reads a byte from RAM024A and passes it to the transmit path atF8E6.

The instruction witness sets024A to91 and00A7 to22: the released pointer
selects91. Changing only the pointer in copied fixture memory to00A7 selects22,
and neither case writes the commanded-AFR variable. The verified OEM bytes
store00A7 there, consistent with the old battery-voltage channel.

The inherited description already correctly explains the logging purpose.
The short title is ambiguous, not evidence of a wrong address. **ALDL channel
source address** is clearer than presenting this Hex word as an AFR target.

## VE selection and its TPS parameters

At7F95, normalized TPS01D9 is compared with FF8B. TPS above that value selects
the main table header49D5. At or below it, RPM coordinate0062 is compared with
the fixed48 boundary at7FA4. A value below48 selects4A88; equality or above
selects49D5. At25 RPM/count the nominal boundary is1800 RPM. The XDF's data
starts49D8/4A8B follow those respective headers.

All18 TPS/RPM/capture-state fixtures agree. Toggling IAC captured-idle bit36.2
does not change this selection. **Main VE** and **Closed-throttle VE** describe
it more directly; the conventional Idle VE title is not itself proof of an
incorrect map address or conversion.

FF8B is also the fuel idle-retention and optional closed-throttle OL threshold.
The old48DA control no longer selects VE. Its surviving consumers are the
RPM-derived filter gate at777B, the BLM transition gate at8DA8, and DFCO spark
floor selection atAAFE. They do not all use the same equality convention.

## Maximum spark retard is a signed angle floor

AAF7 checks the active DFCO-spark bit51.5; AB01's branch after the AAFE
comparison also requires TPS<=48DA to select4148. Otherwise AB0E loads4146.
AB06/AB11 compare the chosen word with command01EE using signed BLT.
If the command is below or equal to the bound, AB17 stores the bound.

The current normal wordFFEE is -18 angle counts, nominally -6.328125 degrees;
the DFCO wordFFF5 is -11 counts, nominally -3.8671875 degrees. Twenty fixtures
cover both states, TPS equality/above and incoming angles below/equal/above
the limits. They implement max(command, signed floor). Later service edits
atAB1D..AB3E can change the command after this clamp.

**Maximum Spark Retard** is defensible shorthand for the allowed negative-angle
limit. The earlier wording overstated its inaccuracy. **Normal minimum spark
angle** / **DFCO minimum spark angle** make the signed storage and comparison
explicit. These are not the separate base-relative DFCO subtraction at4152,
and they are not unconditional final clamps after service overrides.

## New idle names and reproducibility

989C loads9F11, clears B and stores the word at029D. Seed38 produces2600;
a copied-memory seed45 produces2D00. This initializes the runtime integral
and its zero fraction. **Idle-air seed** is concise; it does not imply learned
air survives restart/homing.

C9AD..C9BC subtract16 from coolant byte06, floor at0 and cap at192 to produce
0283. 98E7 loads that coordinate and98EA selectsFF60. Six joined producer/lookup
fixtures verify this chain. The axis is a native coolant coordinate, not degrees
C. Normal production reaches0..192 even though the generic curve definition has
17 knots through256; high knots are not all independently active tuning points
on this normal producer path. **Idle target vs. coolant index** is appropriate.

The maintained non-OEM read register gains5216 and clarifies five existing
shared/changed roles, preserving original roles and other tabs. There is no ROM
runtime writer to add to the write reference. Released Rev B generation now
uses its pinned role snapshot so later read-reference findings do not silently
rewrite the supplied XDF. All released XDF bytes still regenerate unchanged.

```sh
python tools/verify_revb_xdf_labels.py --check-recorded
python tools/verify_revb_xdf_labels.py --rom /path/to/RevB.bin --baseline /path/to/RevA.bin --record
```

The second command records code/calibration excerpts and reports, never a BIN.
Direct reference coverage is bounded by the rooted sweep and its indexed/external
frontiers. It is not a blanket semantic certification of all inherited XDF entries.
