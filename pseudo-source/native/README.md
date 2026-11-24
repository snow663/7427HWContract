# Pseudo-source → native HC11 image: strict composition gate

This is **not** a compiler for C. An HC11 instruction-level simulator
cannot execute `pseudo-source/*.c` files directly. They must first be
compiled with a real 68HC11 C toolchain and linked into an executable
HC11 address space, alongside the existing ASM11 reset and ISR code.

`compose_hc11_rom.py` performs the subsequent, fully deterministic
**image composition** step once the real machine-code sources exist:

- Read separate ASM11 bootstrap S19 and cross-compiled C S19; verify
  Motorola byte counts and checksums.
- Reject ROM region violations, self-overlapping records and any
  ASM11/C collision.
- Read the EXACT `pcm_hc11_c_entry` symbol address from a native
  `nm` listing; never infer an entry from host pointer addresses.
- Require the ASM11 link-word address and its **original unbound
  target** from the assembler listing. Reject an unmatched original word.
- Patch only that two-byte gateway call address; preserve all 32 original
  ROM vector words, with all non-reset entries still pointing to the
  engine-off trap.
- Emit a 48 KiB image mapped to CPU $4000..$FFFF plus SHA-256/placement
  and safety report. Any mismatch **fails without a partial output file**.

Example (only after a native compiler + actual assembler exports exist):

```sh
python3 pseudo-source/native/compose_hc11_rom.py \
  --asm-s19 build/7427_rom.s19 \
  --native-c-s19 build/pseudo_source_hc11.s19 \
  --nm-symbols build/pseudo_source_hc11.nm \
  --c-entry-symbol pcm_hc11_c_entry \
  --entry-word-addr 0x<ASM11_LISTING_ADDRESS> \
  --expected-unbound 0x<ASM11_LISTING_ADDRESS> \
  --out-bin build/7427_simulation_only.bin \
  --out-report build/7427_simulation_only.json
```

The placeholders above must be replaced with actual listing addresses,
not guesses. The builder does **not** certify an HC11 compiler ABI,
stack size/balance, C static/global RAM allocation, IRQ nesting,
hardware peripheral timing, or calibration placement. It cannot bind
future C ISR vectors without explicit vector-specific admission.

A linked output is **for simulation and inspection, not flashing**.
The separately compiled host C regression suite remains authoritative
for source algorithms until a native HC11 toolchain has been verified.

Run the composition gate's independent synthetic fixtures:

```sh
python3 -m unittest discover -s pseudo-source/native/tests -v
```
