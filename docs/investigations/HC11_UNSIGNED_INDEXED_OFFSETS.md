# HC11 indexed displacement correction

The retained-boot port exposed a host CPU error at 737D/7385/738D. With X=5B00,
offsets C7/C8/C9 must read 5BC7/5BC8/5BC9. The simulator's shared indexed-address
helper sign-extended its offset and instead read 5AC7/5AC8/5AC9. The C boot
recovery routine and the existing global-alias formulas used the unsigned
interpretation; the disagreement concerned the CPU fixture.

[NXP AN1283, section 5.1.2](https://www.nxp.com/docs/en/application-note/AN1283.pdf)
specifies the HC11 indexed offset as an unsigned eight-bit displacement. Relative
branch displacements remain signed. `HC11CPU._indexed` now preserves the unsigned
byte and wraps the final address to 16 bits. This shared helper serves byte/word
operands, indexed bit operations and indexed control transfers.

The focused `test_indexed_offsets.py` checks every byte displacement for both X
and Y, including address wrap, and selected word, bit and JMP instructions. A
separate complete relative-branch displacement sweep retains signed semantics.
All three tests pass. Their flat memory adapter deliberately isolates CPU address
arithmetic from internal RAM/peripheral mapping.

This changes the host execution model; it does not change the ROM bytes, the
already documented unsigned address formulas or the physical hardware contract.
Earlier passing CPU comparisons do not prove the corrected high-offset cases.
The full source and simulator suites remain queued for the user's "pull and
merge" instruction; current development uses focused comparisons. Record their
results before claiming regression closure under the corrected CPU.

A decode of the existing rooted alias catalog identifies72 explicit indexed
sites with displacements>=80 hexadecimal. They include the three new boot
counter comparisons and later transmission/diagnostic sites. This is a static
impact inventory, not execution coverage of those72 sites.
