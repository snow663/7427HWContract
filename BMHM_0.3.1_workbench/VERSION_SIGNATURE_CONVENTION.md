# BMHM version signature convention

Starting with **BMHM 0.3.4**, every BMHM build shall carry a version-specific signature in the stock `$31` platform-ID bytes at `$4002-$4005`.

The purpose is operational traceability: the signature is available through the stock data stream, so a saved ALDL log can be matched to the exact BIN revision without relying on file names or memory.

## Encoding

```text
$4002 = major version byte
$4003 = minor version byte
$4004-$4005 = patch/build number, big-endian 16-bit
```

Examples:

```text
BMHM 0.3.4 -> 00 03 00 04
BMHM 0.3.5 -> 00 03 00 05
BMHM 0.4.0 -> 00 04 00 00
BMHM 1.0.0 -> 01 00 00 00
```

The source labels these locations:

```text
$4002  PLATFORM ID WD 1
$4004  PLATFORM ID WD 2
```

## Checksum interaction

The `$31` calibration checksum sums `$4008-$FFFF` and stores the result at `$4006-$4007`. The platform-ID bytes at `$4002-$4005` are outside that checksum range. Updating a BMHM version signature therefore does not require changing the checksum unless some other byte at `$4008` or above also changes.

## Release rule

Before a BMHM BIN is handed off for flashing or logging:

1. write the version signature at `$4002-$4005`;
2. verify the bytes match the file version;
3. verify the `$31` checksum independently;
4. record the final signed SHA-256 in that revision's workbench notes.

A log whose platform-ID signature does not match the expected BIN version should be treated as coming from a different calibration until proven otherwise.
