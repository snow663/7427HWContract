# Factory $1800 code interface and CPU memory decode

Following the actual ROM identifies more than eight unexplained calls. Boot
programs an external chip-select window containing1800; the nine literal
references consist of eight executable calls and one signature read. The
callers expose specific RAM/register results. Together these strongly support
an optional executable-code vector interface. Its exact supplying device and
callee instructions remain unidentified.

## INIT and the decoder settings

7100..710C contains these actual bytes/instructions:

| PC | Bytes | Operation |
|---|---|---|
|7100|8E03FF|LDS #03FF|
|7103|CE1000|LDX #1000|
|7106|8603|LDAA #03|
|7108|A73D|STAA 3D,X: write INIT at103D|
|710A|CE3000|LDX #3000 for subsequent CPU-register access|

The initializer called at711C preserves X and writes305C=00,305D=AC,
305F=CB,305E=00 atCC89/CCA7/CCAB/CCAF. No ordinary rooted direct or
qualified finite indexed writer later remaps these registers. Supplied code
and factory upload retain their separately documented effects.

Using the [NXP MC68HC11F1 data sheet](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
sections4.3.2.2 and4.5, tables4-9..4-12, the programmed decode is:

| Resource | Range / setting |
|---|---|
|CPU registers, INIT03|3000..305F; internal RAM page remains0000|
|CSIO1, enabled by AC|3060..37FF|
|CSIO2, enabled by AC|3800..3FFF|
|CSGEN, base00 / sizeCB&7=3|0000..1FFF,8KB, active low, address-valid|
|GCSPR bit in AC|General select has priority over program select|
|Program select size bits00|64KB selection before competing/internal decode|
|Clock stretch register00|No programmed chip-select wait cycles|

These are consequences of the F1-style register layout, not proof of the
actual CPU marking or board wiring. The8KB selection does not establish8KB
of RAM. Internal resources can take precedence; external devices can decode
fewer address bits or impose additional selection. In particular, a physical
alias between low-memory windows is not excluded by ROM alone.

**1800 lies inside the configured general-purpose external selection, not
inside the relocated CPU registers or either relocated I/O-select window.**
A CPU extended address1800 is not automatically translated to3800 by INIT.

## The opcode evidence specifies executable access

All14,523 rooted instruction starts, occupying34,527 bytes, were decoded
again from the committed hash-identified mapped ROM evidence. Exactly nine
literal references target1800..1817: JSR1800/1803/1806/1809/180C/180F/1812/1815,
and the LDX1800 signature read. A JSR changes the program counter and fetches
instructions at the destination; it is not a store to a peripheral control byte.

F5DC..F5E7 is:

~~~asm
LDX  $1800
CPX  #$7E18
BNE  done
JSR  $180C
done:
RTS
~~~

7E is the extended JMP opcode. If the signature is an instruction prefix, the
third byte completes a JMP to18xx. Three-byte entry spacing across eight
destinations matches the size of that JMP. This is strong evidence for a
jump-vector/code interface, **not proof that each missing entry actually
contains a JMP**, or that the first destination must specifically be1818.

F5DC is invoked in scheduler slot7, repeatedly. The signature check is
independent of0086.6; it is not restricted to a single boot initialization.
Seven other calls require0086.6. The ordinary resident writers clear or
preserve that bit but never set it, so supplied module code is a plausible
owner of enabling the interface. The ROM does not prove who supplied it.

## What each missing routine must expose to its caller

| Entry / call PC | Observable resident interface |
|---|---|
|1800 /8C6A|Called after local AFR calculation. After return8C6D reloads024A and publishes024B. An AFR change therefore needs a RAM024A effect, not merely returnedA. Active local AFR service bypasses this hook.|
|1803 /93D4|Runs before the IAC controller.93D7 immediately clears0038.6 and normal reset/service/control paths follow. There is no explicit scalar-return override of the whole controller. Other state effects can matter.|
|1806 /F5D3|Background hook before A=F7 and store0F00. ReturnedA is overwritten; no explicit scalar result is consumed. The purpose of0F00 is not established by that write.|
|1809 /8EDF|EntryA is the RPM-error magnitude already stored0293;0075.2 records its direction. Returned carry set branches directly to storing returnedA at0299. Carry clear takes the resident computation and reloadsA.|
|180C /F5E4|Signature-qualified recurring connection/service entry. Incoming X is7E18, the successful comparison value. No normal-call scalar result is consumed; the callee must manage any initialization/session/enable state itself.|
|180F /AB66|ReturnedA is saved atAB69, restored atAB75 and used byF550 to multiply word005F. This is an explicit spark-conversion coefficient return channel.|
|1812 /A9E4|Composite spark command01FD is already stored. ReturnedD is not read directly; later code reloads01FD or replaces it through a subsequent resident override. Modifying the command normally requires a RAM01FD effect.|
|1815 /D029|Desired EGR01AE is already stored. A later service override can replace it; otherwise the downstream controller reads01AE. A returnedA alone is not published as a new desired-EGR value.|

These are observable channels, not an invented complete calling convention.
The missing code could also alter other RAM, registers, condition codes, SP,
hardware or control flow. Register preservation and normal return cannot be
assumed just because a specific result channel is visible.

## Two additional signs of an instrumentation/extension context

0086.6 also enables the scheduler's per-slot peak-timing words02D3..02F2.
AtE4F1 it additionally admits a check of0801&03 before closed-loop permission.
0801 has no ordinary resident producer apart from its boot clear and unchanged
foreground self-copy. An extension-owned status input is therefore a reasonable
inference. Profiling/status coupling supports a software instrumentation or
extension interpretation; it does not identify a particular GM development
tool or prove that a normal production PCM supplies the module.

The nearby FF90/FF93/FF96 JMP entries and tail helper words offer callable
resident services, but their intended external callers remain unproven. Their
layout is supporting context, not evidence of a specific absent module body.

## A resident loading mechanism exists, with a hardware precondition

Factory ID01 copies32 bytes from0390..03AF to a received16-bit destination.
Choosing1800 would attempt to place a24-byte vector block and additional bytes
there. Factory ID02 can then call an arbitrary received address, and the
slot7 signature probe can call180C once its required prefix is present.

That is a possible loading/activation route **if that address is backed by
writable executable memory**. The ROM does not prove that GM used this route,
that1800 is physically writable, or that any particular supplied module was
ever present. Forward overlap, retained short-packet bytes and a fresh factory
timer/SP reset retain the semantics in the service contract.

## What is resolved and what evidence would resolve the rest

The address is now tied to the programmed external decode, its accesses are
identified as instruction entry/signature read, and each caller's observable
result channel is documented. There is no ordinary1800 control-register write
hidden in these calls. An external device supplying executable bytes could
still be part of the interface; the chip-select settings do not identify it.

The serial address encoding needs care: normal ALDL reads of encoded1800
are transformed to a word read atCPU0800 byF8C7's ANDA #CF. That is a
transmitter convention, not a CPU memory-map translation or proof of physical
aliasing. Factory0050.3 suppresses that transform. A proposed1800 runtime dump
must therefore establish that it reads the actual CPU address, rather than
this encoded0800 alias.

The remaining unknown is the actual memory response and code supplied at
1800..1817 and its branch destinations. A runtime read of that area together
with0086/0801, or the supplied factory/module image, would distinguish absent
code, JMP stubs, a ROM/RAM module, or board-level aliasing. No hardware result
is inferred from the FF padding in the full-file BIN.

Evidence and reproduction:
- maps/structure/factory_extension_memory_evidence.json
- tools/verify_factory_extension_map.py --check-recorded
- tools/verify_factory_extension_map.py --rom /path/to/BMHM.BIN

Recorded mode reuses the previously verified full mapped bytes; it is not a
fresh read of either original BIN copy. No new simulator feature is included.
