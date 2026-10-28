# Factory indexed ownership, flags and external-interface closure

This pass finishes the **global address-provenance and gate-lifetime
documentation**, and specifies the resident side of the remaining external
and physical interfaces. It does not claim hardware bench completion or
reconstruct code that is not in the supplied ROM.

| Checklist item | Result / evidence | Remaining limit |
|---|---|---|
| All951 rooted explicit indexed-memory PCs | Each has a qualified address expression/context in [global alias contract](FACTORY_GLOBAL_ALIAS_CONTRACT.md) | Dynamic read/caller parameters remain formulas, not invented fixed addresses |
| Interrupt, boot, serial and scheduler contexts |253 procedure entries,1,071 local context rows,657 call bindings | Conditional normal returns and interrupt timing retain their stated assumptions |
| Remaining state-writing helper parameters | All rooted callers bind E58C/F275/F25F/F479; six F2FD calls have exact footprints | Local saved frames stay relative to their own SP |
| Ordinary indexed write destinations | Every non-frame indexed write exceptFABC has a finite conditional footprint | Footprints rely on explicit resident state/admission invariants; no arbitrary-code exclusion is implied |
| Unrestricted factory upload |FABC=word[038E]+0..31, byte-source/latch/dispatch lifetime documented | Actual destination unrestricted; writes wrap atCPU16-bit address level; target hardware response separate |
| Flag and overlapping byte owners |3,846 bit-writer rows;1,415 runtime-address owner rows;45 masked clears included | Value-dependent assignments are marked, not guessed; these counts are not counts of distinct variables |
| Scheduler/service gates |12 named gates /51 writer rows plus [flag lifetimes](FACTORY_FLAG_LIFETIMES.md) | Instruction-time tests do not create a single coherent mode snapshot |
| Extension/profiling enable | No ordinary resident0086.6 setter; boot clear/self-copy accounted for | Independent signature-qualified180C can change it; body absent |
| Shared output ownership | Normal, boot and factory co-writers plus output shadows linked | Issued command, latch effect and physical movement are different observations |
| Eight extension entries | Every call guard and resident continuation documented | Actual1800..1817 code/module ABI remains absent |
| Received callbackFAA5 | Full supplied word and repeat/arming rules documented | Arbitrary supplied code/register/memory/control effects remain unbounded |
| Alternate entriesFF90/FF93/FF96 | Jump bytes/destinations documented; no direct rooted resident references | Intended external callers still need actual caller/runtime evidence |
| CPU versus board-register labels | F1-style register-map match resolves provisional3008/300C/300D/305C..5F names | Package/wiring and proprietary device behavior are separate evidence |
| Physical electrical/mechanical behavior | [Interface evidence matrix](FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md) identifies the missing observation for each interface | No new bench measurement supplied in this task |

The older262-row indexed baseline is preserved as historical analysis, including
its28 previously unknown rows. The new951-PC map gives their global formal
contracts; this does not turn an arbitrary runtime pointer into a singleton
or change the old finite-analysis output to manufacture a zero-unknown count.

## Reproducible files

All generated evidence lives in `maps/structure/`:

| File | Purpose |
|---|---|
| bmhm_ownership_rom_evidence.json | Image/listing identity, entire mapped4000..FFFF byte evidence and scoped counts |
| factory_global_alias_sites.csv | One qualified contract per951 indexed PCs |
| factory_global_alias_contexts.csv | Unmodified finite-analysis results per generic procedure context |
| factory_global_call_bindings.csv | Per-call X/Y/D and target binding; unknown inputs retained |
| factory_global_alias_owners.csv | Direct plus finite qualified indexed byte owners below4000 |
| factory_global_formal_writers.csv | Sole non-frame write without finite footprint:FABC supplied destination |
| factory_global_flag_writers.csv | Bit-level effects including clears, mask preservation, self-copy and dependent full-byte writes |
| factory_global_gate_lifetimes.csv | Writer join for the12 documented scheduler/service gates |
| factory_global_hardware_accesses.csv |131 concrete hardware-byte access rows, with wildcard interfaces separate |
| factory_external_hook_contracts.csv | Eight external calls with ROM-checked enable/signature guards and resident continuation roles |

Fresh verification uses the **actual full image**, with its SHA checked first:

```sh
python tools/verify_factory_ownership.py --rom /path/to/BMHM.BIN
python tools/verify_factory_ownership.py --rom /path/to/other_stock_BMHM.bin
```

The two supplied filenames have identical image identity; checking both verifies
the copies, not two different factory calibrations. `--check-recorded` reproduces
the committed mapped bytes and artifacts; it is not another independent ROM read.
`--write --rom ...` regenerates the evidence. The original HAC is unchanged.

## What can be crossed off, and what remains

The named resident subsystem dossiers, rooted structure, indexed-address
provenance, writing-helper bindings and scheduler/service flag lifetimes now
connect in one documentation chain. This does not grade every whole-byte
assignment as a semantic proof of every bit, prove all interrupt interleavings,
or establish a whole-firmware understanding percentage.

The outstanding evidence is now specifically identified: actual external
extension/caller code, any supplied factory callback/upload session to be
analyzed, and physical CPU/board/actuator observations in the interface matrix.
An unconditional whole-machine write set cannot exclude code that the factory
protocol explicitly allows a tool to supply. General semantic closure of
every flag under every possible mode/interleaving remains stronger than the
documented local effects and controller contracts; it is not silently declared
complete by the size of the generated indexes.
