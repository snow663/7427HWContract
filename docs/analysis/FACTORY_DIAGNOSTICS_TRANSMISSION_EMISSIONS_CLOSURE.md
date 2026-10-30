# Factory diagnostics, transmission and emissions documentation closure

The named resident diagnostics, transmission and emissions software is now
documented from the stock BMHM ROM. This extends the completed fuel, spark,
IAC and speed/governor derivations through their previously open gear,
fault, transmission-spark and emissions-output owners. It is a bounded
software-documentation closure, not a whole-ROM understanding percentage.

| Area | Completed resident scope | Contract |
|---|---|---|
| Diagnostics | Local engine/transmission monitors, EGR response/position tests, fault reaction masks, boot retention/checksums, log persistence, flash-code/lamp state, masked clears and local service timeout/overrides | [Diagnostics](FACTORY_DIAGNOSTICS.md) |
| Transmission | Switch/pattern/capture/TPS/temperature inputs, gear and descriptor priorities, shift observation, adaptive cells, pressure/current loop, electronic and nonelectronic TCC, shift lamp, transmission spark requests and shared output writers | [Transmission](FACTORY_TRANSMISSION_CONTROL.md) |
| Emissions | EGR feedback/closed-reference learning/I-P/duty/fraction, purge qualification and adaptive duty, AIR, catalyst estimate, manifold and AC/shared-output selectors | [Emissions](FACTORY_EMISSIONS_CONTROL.md) |

The scope includes optional resident branches even when their stock option
is disabled. A reserved flash code or literal RTS stub is recorded as such;
it is not assigned a nonexistent monitor. The nine direct peripheral VSS
readers from the earlier pass now have documented owners. All 39 previously
listed direct raw/filtered VSS readers are connected to contracts; that
denominator does not establish all indexed speed aliases in the program.

## Evidence

Authority is the full 65,536-byte stock image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Both supplied stock BMHM filenames must match. CPU4000..FFFF equals full-file
offsets. CPU0000 is RAM; no low-memory executable is inferred from file
padding. The truck's 2.bin remains a separate calibration-value authority.

| Artifact under maps/structure | Purpose |
|---|---|
| bmhm_dte_rom_evidence.json | Image/source identity, reviewed instruction/data excerpts and scoped counts |
| factory_dte_blocks.csv / roots.csv | Reviewed spans and local CFG roots linked to the contracts |
| factory_dte_instructions.csv / branches.csv / calls.csv | Actual opcodes, memory widths, branch conditions, targets and call boundaries |
| factory_dte_states.csv | Selected state roles, reviewed direct readers/writers and other listing candidates |
| factory_transmission_pointer_sets.csv | Direct word arrays kept distinct from descriptor headers |
| factory_transmission_descriptors.csv | Header-derived priority/gear columns, full-word pointers and RAM/calibration/null classification |
| factory_diagnostic_bits.csv | All 72 ROM flash-table identities, live/retained/candidate banks and clear/log/lamp masks |
| factory_dte_listing_discrepancies.csv | Covered differences from inherited HAC; byte authority retained locally |
| factory_rpm_vss_consumers.csv | Updated 39-reader owner crosswalk |

The reviewed evidence covers 62 instruction spans,7,628 instruction starts,2,027 branch
rows,142 local CFGroots,153 selected states,20 priority descriptors and 35 direct
pointer arrays. Twelve covered listing differences are recorded locally. These
counts include shared helpers and previously reviewed code; they are not counts
of newly understood disjoint functions.

The original HAC is unchanged. New local byte inventories take precedence
for their covered instructions; this does not silently expand the older
global partial overlay or its whole-listing counts. Inventory generation
checks bytes and structure; the human reductions of controller equations
and lifetimes are distinct evidence from that deterministic regeneration.
Thirteen new bounded execution tests cover selected high-impact branch/retention rules,
not a complete transmission or emissions operating simulation.

```bash
python tools/verify_factory_dte.py --rom /path/to/BMHM.BIN
python tools/verify_factory_dte.py --check-recorded
python -m unittest discover -s tests -p 'test_factory*.py'
```

## Findings that materially change interpretation

- D8FE implements ordered **data-pointer selection**. It returns complete
  words and stops on the first selected null pointer. A stop/no-selection
  failure retains a row address inX; it does not necessarily returnX=0.
- E58C's no-new-count exit can return the remaining timeout in D while its
  saved speed word remains unchanged. The caller and the record therefore
  do not always contain the same quantity.
- Fault detection, log admission, retained storage and lamp request are
  separate state machines. Existing candidates are intersected across
  observations; local fault recovery can be limited by retained counters.
- The ROM flash table identifies16.4 ascode 16 and 17.5 ascode 24. Electronic
  and manual-option paths both own 17.5. Names inherited from comments are
  not sufficient to identify a live bit.
- Service, voltage and diagnostic modes can override EGR/purge/AIR/TCC
  hardware writes after normal calculations. The final register value is
  not always the stored controller command.
- The post-spark EST monitor ABCB is now documented, closing that previously
  named resident diagnostic boundary. Its ASIC feedback interpretation is
  still a hardware interface.

## What remains separate

The full SCI/ALDL framing and command/factory-test machines are now documented
in the [serial/service closure](FACTORY_SERIAL_SERVICE_CLOSURE.md). The
[global structure audit](FACTORY_GLOBAL_STRUCTURE_AUDIT.md) additionally reviews
rooted reachability, alternate entry candidates and direct state owners.
Remaining scope is global contextual/indexed aliases and flag lifetimes,
intended external-entry callers, opaque low-memory extensions, and physical
hardware/electrical/interrupt behavior requiring additional evidence.

These are explicit remaining items, not reasons to reopen the documented
resident diagnostics/transmission/emissions control calculations. No claim
of fully understanding every byte of the factory program follows from this
closure.
