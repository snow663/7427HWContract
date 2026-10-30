# Observed1800 readback

The user flashed the previously prepared
`BMHM_0.3.12_ALDL_1800_READBACK.bin` and supplied this RealTerm exchange:

```text
request echo: F4 56 05 B1
reply: F4 6E 05 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 99
```

The reply has28 bytes: three header/echo bytes,24 data bytes and checksum99.
The complete reply sums to0 modulo256. The supplied data is all zero at
CPU1800..1817. The current saved probe image has SHA-256
`c907d853cb1047456e5d4588c836a7859369d1c8e6eb783c9703539bf90a1010`.
Executing this exact probe's serial path in the local instruction fixture
with a1..24 RAM pattern verified its address range and reply framing; that
pattern was a fixture, not the truck observation.

The current presence check would see0000 rather than7E18 and skip180C.
One readback does not establish physical RAM backing, writability, aliasing,
all reset states or a stable repeated sample. Key-on/engine-off was the
requested test condition; the actual operating condition was not explicitly
confirmed in the supplied response.

The user subsequently restored the regular0.3.12 tune. The optional module and
loader are outside the initial replacement-firmware scope. This observation
does not replace the stock BMHM image as the factory-source authority.
