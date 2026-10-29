# Factory serial, service and test documentation closure

The resident SCI/ALDL receiver/transmitter, ordinary service-command lifecycle,
and manufacturing-test loop are documented from actual BMHM bytes. The callback
is closed as a **payload-supplied full word with no resident target whitelist**,
not as an unresolved fixed dispatch table waiting to be discovered.

| Completed software | Contract |
|---|---|
|SCI initialization/interrupt priority; framing/checksum/error paths; ID/command/page tables; raw, live and requested-address replies; optional broadcast|[Serial protocol](FACTORY_SERIAL_ALDL_PROTOCOL.md)|
|Payload commit/retention; controller override ownership; clear edges; session and duration expiry; factory admission/upload/callback/output cycling|[Service and manufacturing test](FACTORY_SERVICE_AND_TEST.md)|
|Joined expiry/cleanup order; retained raw outputs; accepting-checksum windows; callback retarget/restart; optional caller precedence|[State transitions and optional behavior](FACTORY_JOINED_STATE_AND_OPTIONAL_BEHAVIOR.md)|
|Rooted control graph, disconnected candidates, table/code boundaries, and remaining ownership interfaces|[Global structure audit](FACTORY_GLOBAL_STRUCTURE_AUDIT.md)|

## Authority and reproducibility

Full stock ROM:65,536 bytes, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Both supplied BMHM filenames are checked separately. CPU4000..FFFF equals
full-file offsets4000..FFFF; CPU0000 is runtime RAM. The truck's2.bin remains
a separate calibration-value source. The inherited HAC file is unchanged.

`tools/verify_factory_serial.py` produces byte excerpts plus instruction,
branch, control-edge, descriptor, command, page-selector, live-pointer,
selected-state-owner, output-row and listing-discrepancy maps under
`maps/structure/factory_serial_*` and `factory_test_output_rows.csv`.
`bmhm_serial_rom_evidence.json` records their image and listing identity.
It covers15 local spans,1,075 unique instruction starts,212 branch rows,
21 descriptors,22 command-table slots,376 live-pointer entries and43 selected
states. Six covered listing discrepancies include previously known heartbeat
rows and the newly checkedFA72 threshold. These are scoped inventory counts,
not disjoint functions, instruction-execution coverage or a completion percentage.

```bash
python tools/verify_factory_serial.py --rom /path/to/BMHM.BIN
python tools/verify_factory_serial.py --check-recorded
python tools/verify_factory_global_structure.py --rom /path/to/BMHM.BIN
python tools/verify_factory_global_structure.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_*.py'
```

Recorded verification reproduces the committed excerpts/maps. Full-image mode
first checks the entire image hash, then reads instruction and table bytes.
Neither regeneration nor the existing bounded tests establish physical SCI
timing, arbitrary callback behavior or a complete proof of interrupt concurrency.
This pass finishes documentation and evidence; it adds no simulator feature.

## Findings that change interpretation

* Addressed reply lengths include the command echo. Engine N=64 contains63
  data fields, not64 pointer reads. Word aliases use one live LDD and a saved
  companion byte; they do not re-read the second pointer entry.
* Length/checksum acceptance does not impose per-command payload size. RX
  stores and session-bit changes precede final checksum acceptance. A short
  service packet or factory upload can use retained bytes.
* Factory ID02 repeatedly calls the received word; ID03 also replaces that
  word and only invokes it after an earlier arm. Its destination is not a
  legal-target list encoded somewhere else in ROM.
* FA72 is `CMPA #$28`. The listing's40-hex operand would give the wrong
  manufacturing-test input window.
* Ordinary expiry preserves most payload bytes. Some downstream selectors
  read raw override fields without a local active-service test.
* The joined pass corrects the service threshold words to51BB=FFFF and51BD=0000.
  OrdinaryAE85 callsF781 thenF64E consecutively; idle expiry can rearm a held
  engine-clear request and executeF333 again before cleanup. Thirty selected
  state/optional transitions have actual-ROM execution witnesses.

## Remaining scope

Resident serial and manufacturing-test **software** are closed to the same
bounded standard as the preceding engine, IAC/speed and DTE contracts. The
[ownership closure](FACTORY_OWNERSHIP_CLOSURE.md) now supplies all951 indexed
address contracts, writing-helper bindings, gate lifetimes and the graded
external/physical interfaces. Alternate-entry intent remains unproven.
Arbitrary received code and low-memory extension contents are not present in
the stock ROM and cannot be assigned effects from file padding or a guessed
whitelist.
