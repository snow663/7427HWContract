# BMHM version signature / ALDL contract

## Source-backed ALDL behavior

The stock `$31` 8192-baud Mode-1 message does **not** serialize the platform-ID words at `$4002-$4005` in the normal data stream used by the current logger.

The message map at `$51F8` explicitly serializes:

- output byte 1 from `$4000` — PROM/EPROM ID word MSB
- output byte 2 from `$4001` — PROM/EPROM ID word LSB

The calibration header itself is:

- `$4000-$4001` — EPROM ID word
- `$4002-$4003` — PLATFORM ID word 1
- `$4004-$4005` — PLATFORM ID word 2
- `$4006-$4007` — checksum
- `$4008` — `$31` EPROM ID byte / mask byte

The 2026-08-25 BMHM 0.3.4 log reports `PROM ID = D`. BMHM 0.3.4 still carries `$4000-$4001 = 00 0D`, while `$4002-$4005 = 00 03 00 04`. This proves the current stock log item is reading `$4000/$4001`, not the platform-ID words.

## Release rule from the next BMHM build forward

Use both representations:

1. `$4002-$4005` remains the canonical 4-byte software version signature:
   - byte 0 = major
   - byte 1 = minor
   - bytes 2-3 = patch/build, big-endian

2. `$4000-$4001` becomes the short **ALDL-visible build signature** so the ordinary stock log identifies the BIN without a custom definition.

Recommended encoding for the current 0.x series:

- BMHM 0.3.5 -> `$4000-$4001 = 03 05`, platform ID = `00 03 00 05`
- BMHM 0.3.6 -> `$4000-$4001 = 03 06`, platform ID = `00 03 00 06`
- BMHM 0.4.0 -> `$4000-$4001 = 04 00`, platform ID = `00 04 00 00`

For a later major version, revise the compact 16-bit convention if needed; the 4-byte platform signature remains authoritative.

All of `$4000-$4005` are outside the `$31` checksum range, which begins at `$4008`, so version stamping does not alter the stored calibration checksum.

## BMHM 0.3.4 caveat

The distributed signed 0.3.4 image stamped only `$4002-$4005`. Its stock Mode-1 log therefore still shows the inherited PROM ID `D` and cannot be uniquely identified from that field alone. Do not infer the 0.3.4 version from `PROM ID = D`; use file provenance/SHA for that build.
