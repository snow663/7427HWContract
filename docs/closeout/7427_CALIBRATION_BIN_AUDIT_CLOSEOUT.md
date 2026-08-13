# 7427 Calibration / BIN Audit Closeout

## Numeric authority

Audited target supplied from `31.zip`:

```text
archive member: 31/BMHM.BIN
size: 65536 bytes (0x10000)
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
MD5: bba1f40841e710be5533bf0d96479ffb
```

This file is the numeric authority for stock-equivalent BMHM calibration reconstruction.

Source/semantic authority remains the `$31` BMHM/HAC executable/disassembly and calibration extract.

## Full source-record audit

The complete `31_HAC_calibration_extract_nowrap.html` record set was compared against the 64 KiB BMHM image using the repo audit rules.

```text
records audited:            11,916
exact byte/word matches:    11,700
value mismatches:              120
source-width errors:             96
outside-BIN records:              0
odd-address FDB reviews:        212
label-width review rows:        138
full correction/review rows:    437
source parse errors:              0
```

The existence of mismatches is not a failure of the closeout. The purpose of the audit is to prevent source/disassembly values from silently overriding production ROM bytes.

## Hard discrepancy classification

| Class | Mismatch | Width error | Production impact |
|---|---:|---:|---|
| production numeric mismatch | 4 | 0 | yes; BIN value must be used |
| source label-address typo | 2 | 0 | yes; repair address mapping, do not overwrite actual bytes at wrong label |
| duplicate/phantom source record | 1 | 0 | yes; remove phantom record from reconstruction |
| remote-broadcast/service layout defects | 113 | 95 | no for production replacement scope |
| transmission calibration layout review | 0 | 1 | excluded |

## Reviewed production corrections

Machine-readable authority:

`maps/closeout/calibration_bin_production_correction_overlay.csv`

### `$4146/$4148/$414A` spark retard limits

HAC source declares each as:

```text
FDB 65534 = FF FE
```

BMHM production ROM contains:

```text
FF F5
```

The executable consumes these words as maximum-retard limits. Stock reconstruction therefore uses `FF F5` while preserving the source semantic roles.

### `$4C80/$4C81` DFCO table label defect

The second DFCO RPM-vs-coolant table declares `ORG $4C8D`, then correctly emits:

```text
$4C8D = 80
$4C8E = 72
$4C8F = 68
```

The next two source labels incorrectly repeat `L4C80/L4C81` for values `64/56`. Sequential placement proves they belong at:

```text
$4C90 = 64 (40 hex)
$4C91 = 56 (38 hex)
```

The production BIN confirms exactly those bytes at `$4C90/$4C91`. Real `$4C80/$4C81` remain `105/105` (`69/69` hex) from the preceding table. Therefore this is an address-label correction, not a request to replace ROM bytes at `$4C80/$4C81`.

### duplicate `$4EDB` IAC cold-offset-delay record

The preceding IAC table legitimately ends with:

```text
$4EDB = 70 decimal = 46 hex
```

The HAC source then repeats `ORG $4EDB` and declares another `L4EDB FCB 60 ; Max time 60 sec?`.

That second record is not present in BMHM. More importantly, executable code at `0x94D8` and `0xA04C` loads the IAC cold-offset-delay lookup base as **`#$4EDC`**.

Therefore the second `$4EDB=60` source record is a stale/phantom source artifact. It must be omitted. The production cold-offset-delay table begins at `$4EDC`.

### `$50ED` integral-gain table

HAC source declares:

```text
L50ED FCB 0
```

BMHM production ROM contains:

```text
$50ED = D0
```

Executable code at `0x8F5F` uses the integral-gain lookup rooted at `$50E8`. Therefore `$50ED=D0` is a real production calibration correction and must be taken from the BIN.

## Remote broadcast/service discrepancies

The `$518F-$55F4` `$31` remote-broadcast/polling-format area accounts for:

```text
113 value mismatches
95 source-width errors
```

The source includes mixed byte/word pointers, duplicated/misaligned labels, and apparent byte-order/layout transcription defects. This area is optional diagnostic/service behavior and is outside the standalone production engine-control scope.

If remote broadcast is later retained, reconstruct it from the BMHM ROM bytes and executable consumer semantics; do not import the suspect source operands directly.

## Transmission-only layout review

One source-width problem is in the transmission calibration region and is excluded from the current standalone engine-control replacement scope. Preserve the BMHM byte value if that feature is ever reintroduced.

## Alignment / address review

The audit recorded every odd-address FDB and every label-width anomaly rather than silently normalizing them.

An odd source word address alone is not treated as proof of a bad value. When source bytes and BIN bytes match, the ROM remains authoritative and the alignment metadata remains available for implementation review.

## Closeout decision

The calibration category now satisfies its defined semantic-production completion standard:

- target raw BIN identified and hashed;
- every directly extracted labeled record compared against the actual 64 KiB image;
- numeric mismatches exposed;
- source-width/address defects exposed;
- production-impact discrepancies reviewed individually;
- machine-readable production correction overlay committed;
- optional service/transmission defects isolated from production engine control;
- stock-equivalent reconstruction rule fixed to **BIN numeric value + executable semantic meaning**.

Therefore:

```text
calibration / tuning extraction = 100% — FROZEN
```

Reopen only for contradictory ROM/executable evidence or expansion of the retained feature scope.
