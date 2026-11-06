# Custom 7427 TunerPro definitions

These are **64 KiB, full-address** XDFs. File offset equals CPU ROM address;
the XDF base offset is zero. They are adapted from the user-supplied
`Advanced $31 TP5 v251.xdf`, author **93V8S10**. The original bytes are retained
in the compressed source archive with their SHA-256 in the source contract.

| Definition | Matching program |
|---|---|
| [7427_0.3.12_RevA.xdf](7427_0.3.12_RevA.xdf) | The current engine-only spark/idle Rev A image, SHA-256 `d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e` |
| [7427_Manual_Idle_DEV.xdf](7427_Manual_Idle_DEV.xdf) | The single-controller manual-idle development overlay, SHA-256 `264beb0140e470a8d63a83da74f460fb8864b6027711a26207b308fe9ae2d0b4`; no matching BIN has been released |

**Use the Rev A definition with the current Rev A BIN.** The development XDF's
`$9F00..$9F26` controls are data only in the replacement layout. Those addresses
contain executable code in Rev A. TunerPro does not enforce the documented
image identity simply because it is written in an XDF description.

After ordinary calibration edits, the complete image hash changes. The
read-only verifier also checks the protected program/high-ROM fingerprint so
it can recognize a compatible tuned copy without requiring the pristine hash:

```sh
python tools/verify_custom_xdf.py --rom /absolute/path/to/your_full_64K.bin
```

It identifies the matching definition and verifies the additive ROM checksum.
It rejects a different program layout instead of selecting by filename or
mask number. This fingerprint protects the resident high-ROM program/data and
the engine helper allocation, with only reviewed custom high-ROM calibration
excluded. It does not independently audit every low-ROM calibration edit.

## Corrected and added controls

- One active base spark table is shown, with the retained main bias included
  in its displayed degrees. The retired closed-throttle table and separate
  idle/transient correction tables are omitted. Other retained spark
  corrections and command limits still apply after the base table.
- `$4152` is correctly labeled **base DFCO spark retard**. Its comment explains
  why setting it to zero is not a universal disable. Slow/fast recovery gains
  and the normalized-TPS selector are named by their traced functions.
- `$FF60` exposes all 17 knots of the custom idle target, scaled by 12.5 RPM per
  byte count. Rev A still has a separate `$4F50` startup curve; the development
  controller uses FF60 for both startup and running.
- The custom fuel-policy flags at FE9F and the fuel idle/OL TPS thresholds at
  FF8A/FF8B are included. The global OL flag also neutralizes BLM and the
  INT-derived additive correction. INT is not presented as another multiplier.
- The supplied XDF misidentified 4F23 as an A/C decay period and 4F24 as air.
  Rev A now correctly shows extra air at 4F23, its hold at 4F24, and qualification
  delay at 4F25. The replacement removes those controls.
- The development XDF adds the complete 39-byte single-controller calibration:
  one cold-air curve and 19 scalar controls for baseline, startup, capture,
  P/I, limits, follower, stall and A/C. The three fractional air words are
  unsigned big-endian Q8.8. Internal air units are **not motor steps or measured
  percent airflow**.
- Removed transmission, emissions, VSS, governor, old Park-entry, unused fuel
  branch and diagnostic controls are omitted, including removed functions
  whose old calibration bytes remain physically present in ROM.

The new curves use the native coolant lookup index from RAM 0283, with knots
0,16,...,256. They do not label those indices as degrees Celsius. The last
knot is an interpolation endpoint; maximum byte input is 255. Existing legacy
engine tables retain their supplied axis labels and conversions unless a
correction is specifically listed here.

The development IAC capture/release thresholds and the retained fuel idle
classifier are separate consumers. Defaults match, but the fuel classifier's
RPM margins remain fixed at +100/+200 RPM. Keep both consumers aligned when
changing the IAC thresholds; this definition does not install code changes.

## Checksum and validation

The supplied checksum entry is preserved: additive sum of bytes 4008..FFFF,
modulo 65536, stored big-endian at 4006. The original Rev A checksum is 6D36.
The checksum scalar is documented as a stored result, not a tuning control.
The verifier checks the stored result after a TunerPro save. No ROM is written,
repaired or exported by these tools.

The commands below run from a repository checkout. A download bundle contains
the two definitions, this guide and the validation report; it does not contain
a ROM image or the full repository/tool dependencies.

```sh
python tools/build_custom_xdf.py --check
python tools/verify_custom_xdf.py
python -m unittest discover -s tests -p test_custom_xdf.py -v
```

Checks cover XML parsing, contiguous edit extents, row/column dimensions,
unique IDs, math links, category references, removed allocations, complete
manual calibration coverage, custom conversions and in-memory edit round trips.
Image-specific tests additionally check the exact Rev A and development
layout, code-edit rejection and checksum behavior. The definitions have not
been opened in a native TunerPro GUI here. Remaining inherited engine
conversions are carried forward from the supplied XDF, not newly proved by
these structural checks.

[custom_xdf_manifest.json](custom_xdf_manifest.json) records retained/omitted
source items, profile identity and generated-file hashes. The builder checks
the manual-idle assembly identity to prevent silently reusing a definition
after that layout changes. To update its reference identities, supply the
exact reviewed Rev A image to `build_custom_xdf.py --record-identities`; this
creates an overlay in memory only. Rebuild and rerun the checks together with
future firmware changes.
