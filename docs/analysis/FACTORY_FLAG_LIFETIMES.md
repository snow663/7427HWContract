# Factory flag ownership and lifetimes

This joins direct bit operations, full-byte/word mutations, indexed boot clears,
45 diagnostic AND-mask updates, and foreground self-copy writes. The ROM and
alias assumptions are defined in the [global alias contract](FACTORY_GLOBAL_ALIAS_CONTRACT.md).
The generated3,846 bit-writer rows distinguish **set, clear, preserve,
self-copy, and value-dependent whole-byte/word mutation**. A writer's local
effect does not prove that its calling path is admitted.

The51 gate-writer rows concern the12 named gates below. These are per-writer
records, not51 independent flags. Other controller flags retain their detailed
lifetimes in the completed subsystem contracts and their global co-writers in
`factory_global_flag_writers.csv` / `factory_global_alias_owners.csv`.

## Reset is not one universal zeroing operation

| Region | Initialization | Lifetime consequence |
|---|---|---|
|0036..00FF,0100..029C,0800..08FF | Unconditional clear on the reviewed boot path | Busy/pending, shared service flags, extension enable and controller working words start zero before local seeds |
|0000..000A,000B..0035,029D..034D | Clear only if retained diagnostic checksum validation rejects | Callback-arm/phase/trap byte, live/retained diagnostics and learned state cannot be assigned unconditional zero merely from the helper definition |
|0360..03FE | Separate unconditional byte loop | Serial/session/payload fields clear;03FF excluded |
|02F8..032B | Separate52-byte validation and conditional80 fill | Transmission banks/checksum use a distinct retained-state scheme |
|0002 | Explicit7433 seed0E in ordinary initialization | First normal main pass selects slotF, independently of retained checksum acceptance |

Factory admission71B4 precedes ordinary controller initialization but follows
the unconditional working/serial clears. It sets0044.0 and clears0001 as part
of its own branch. A warm restart, retained-state acceptance, reset/trap cause,
and a fresh factory admission therefore have different state histories.

## Scheduling and mode gates

| Flag | Establishing owner | Clearing/preservation and consumer lifetime |
|---|---|---|
|001A.5, special fast-group gate |71FA on configuration/checksum failure, paired with retained000F.5 and checksum0015 refresh | Conditional boot clear can erase it; F333's maskD9 clears it; F380'sE7 preserves it; refresh preserves it.79D9 tests it on each main pass |
|0086.6, extension/profiling enable | **No reviewed ordinary resident setter** |716A clear initializes it0; refresh preserves it; other direct bit operations on0086 do not touch6. See connection-hook exception below |
|0044.0, factory mode |71B4 after ADC/raw input qualification |716A boot clear initializes0; normal resident flag operations preserve bit0.794E diverts every timer entry intoFA5B while set |
|004F.2, busy |7989 before main-pass body |7A52 clears underSEI at tail;7974 stack-recovery clear;716A boot clear.797D tests after ordinary tick service, so reentry still runs7B6D |
|003A.5, pending |7985 on a busy timer reentry |7A7D clears under tail masking beforeCLI/catch-up;716A boot clear. It is one coalescing bit, not an arrival counter |
|0051.2, refresh request |7B69 in slotF |74B0 clears after foreground reaches0900;716A boot clear. SlotE checks an outstanding request and can latch0004.2 |
|0001.0, callback armed |FA9F for accepted factory ID02 |71B7 clears on factory entry;FAAD clears on ID01 upload; conditional boot clear may clear. ID03 requires an already armed latch and uses the current received pointer |

### What closes the extension-enable question

The earlier direct sweep found no setter and could not exclude an indexed
producer. The new writer join identifies both non-direct owners: the boot-clear
word storeF31E and foreground self-copy7492. Neither sets0086.6. The other
ordinary resident mutations of0086 alter bits0/3/7, not6. Thus there is no
ordinary resident enable transition hidden in the reviewed indexed writers.

However, **F5DC does not require0086.6**. It reads the runtime word1800,
compares7E18, and calls180C on a match. That supplied implementation can set
the enable bit or change anything else. Factory uploadFABC and callbackFAA5
can also change it. Therefore the justified conclusion is conditional:

> With the reviewed boot clear, no supplied-code mutation, and only the
> documented resident writers,0086.6 remains zero. A matching connection hook
> is a separate external entry, even while that bit is zero.

This explains a possible enable interface without inventing the hook's body,
declaring the extension permanently dead, or assuming file-offset1800 padding
describes runtime memory. The physical/external contract lists each call site.

### Why a clear writer does not prove recovery from special mode

F333 clears001A.5 through F346 using the mask atF37B. The sole resident call
is F74C inF64E, reached atAEA0 insideAE85.79D9's ordinary fast-group gate
requires001A.5 **clear** before7A14 callsAE85. The special branch retains the
slot table but has no other rooted directF64E/F333 caller. Consequently that
clear operation does not, by itself, establish that ordinary serial service
can recover an already active special fast-group mode.

The failure boot path sets the retained fault and refreshes0015 before its
following checksum comparison. It must not be modeled as automatically failing
that comparison and taking the conditional clear. Reset/revalidation, supplied
code and arbitrary uploads retain their separate possibilities. F380 preserves
the bit, so transmission clear is not an alternative local proof of recovery.

## Shared service and communication flags

| Flag | Producer / qualification | Cleanup and ordering |
|---|---|---|
|0042.0/.1, addressed session | F93F/F948 on matchingF4/F5 ID, before length/checksum acceptance | Accepted command00 clears its bit; F781 idle expiry clears both. A rejected later frame does not undo the earlier set |
|003B.4, engine service | F715..F720: engine session and038E=04 | F777 clears on session loss or cooldown036A; clear/reset requests are processed before final engine cleanup; payload suffix remains |
|003B.3, transmission service | F677..F68A: transmission session,0399=04,036A=0 | F712 cleans service plus0103/010A/0111/0118 when session/cooldown gates fail |
|003B.2, shared monitor/service gate |79C8..79D6 recomputes it from0051.3 or003B&18 underSEI/CLI | Other003B bit writers and masked copies must preserve it; it is not another received-packet bit |
|003B.0/.1, clear requests | Valid ordinary0A acceptance sets device-specific request | Next ordinary accepted packet clears both first; F64E consumes them through0045 edge latches. Session expiry clears these requests but not every service flag |
|0045.4/.6/.7, request edge latches | F64E latches BLM reset/transmission clear/engine clear on admitted requests | Low request rearms; idle expiry clearsD0. Repeated held request is not repeated erase/reset |
|003B.7, pending TX companion |F8CF after live word read saves low byte0366 |F8D4 emits/clears on following payload slot; checksum/end selection has priority. Abort does not imply all serial flags were reset |
|003B.6/.5, optional broadcast ownership/contention |F602 sets ownership;F5FE/F602 detects previous owner and marks contention | CompletionF81E releases ownership; stock zero schedule excludes broadcast selection, not ordinary service/TX behavior |

Engine and transmission command blocks share a receive source but have distinct
session/service lifetimes.0392.0's O2/I/P users are indexed at86FD/E49E.
Their polarity differs between I/P control and closed-loop admission, as the
[fuel-learning contract](FACTORY_CLOSED_LOOP_AND_LEARNING.md) specifies. Payload
retention must not be replaced with a fictitious independent “force closed loop”
flag or an atomic service transaction.

## Live faults, candidates, retained faults and bit masks

For bankj0..8, live0016+j, candidate0056+j and retained000B+j have different
owners and ages. E132 seeds/intersects candidates; qualifying persistence
unions them into retained bytes and refreshes0015. Fault removal need not
erase retained data or reset recovery counters. F333/F380 mask all or selected
banks differently and perform their own counter/state cleanup.

`factory_global_flag_writers.csv` includes both bytes of a word clear and the
45 exact indexed AND-mask destinations. A preserved bit in an AND store or
foreground self-copy is explicitly marked **preserve**, not counted as a new
setter. A full-byte/word mutation without established value flow remains
marked value-dependent, not assigned a guessed bit value. The diagnostic,
IAC, fuel, spark, transmission and emissions contracts specify admission and
value flow for their controller flags.

## Output shadows and preemption boundary

004B/004C/004E are shared output/input-shadow state. IAC changes its phase
field in004C, transmission C522 merges the gear pattern, and the other bit
owners listed in the IAC/output contract share the byte. F400 flushes shadows
to board registers and samples3064→004D. A target/position count, shadow
change, latch write, and a physical step are separate events.

The new owner map includes normal, boot and factory direct hardware writers.
It does not collapse them into the last normal controller to run. For example,
factory mode bypasses the normal scheduler and writes3062 and several ASIC
command words directly; its row publication masks interrupts around3FFC RMW.

SEI/CLI protects the named I-bit critical regions, not every device/bus event
or every entire controller transaction.79D9, the phase tests and later service
tests sample their bytes at their own instructions. No coherent mode snapshot
is invented across intervening calls. Pending/busy flags explain the resident
handoff but do not prove absence of all nested interrupts, XIRQ/reset effects,
stack recovery failures or device read side effects. Those remain graded in
the [hardware boundary contract](FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md).

## Independent-reconstruction contracts

The [equivalence information ledger](FACTORY_EQUIVALENCE_INFORMATION_GAPS.md)
connects selected flags to interrupt-mask context and output-changing event
order. It verifies the per-block refresh mask, both resident async-fuel caller
masks, pre-busy versus busy TOC3 reentry, acknowledged clear-request replacement,
short service-payload retention and distinct trap/reset/XIRQ handlers.

The [253-entry structural I-mask table](../../maps/structure/factory_interrupt_mask_contracts.csv)
adds normal-RTS postconditions:193 preserve I,16 return I clear,26 depend on
path/input and18 have no normalRTS return. Both branch arms and conditional
opaque returns remain explicit. This is not a whole-CCR, stack-depth, timing
or feasible-interleaving proof. The ledger separates further ROM extraction
from actual device/board/module information.
