# Memory constraints and placement decisions

The final linker layout is not assigned yet. This file separates observed
stock mappings from our selectable code/calibration partition.

| CPU range/resource | Current evidence | Design consequence |
|---|---|---|
|0000..03FF|Stock uses internal working RAM and stack; F1-style map provides1KB|Budget named state, retained data, interrupt frames and C stack together|
|0800..08FF and other low external windows|Resident software accesses them; board backing/aliases need their own evidence|Do not declare the entire general chip-select window available RAM|
|3000..305F|CPU registers after stock INIT=03|Preserve the real register addresses and relocation sequence|
|3060..3FFF|Configured external I/O selections include board/ASIC transactions|Drivers retain access widths/order and explicit hardware semantics|
|4000..FFFF|Mapped stock-ROM address space,48KB visible in the supplied image|Our executable/calibration regions must fit actual fitted/emulated memory and decode|
|FFD6..FFFE|Twenty-one stock vector words|Vector addresses stay fixed; handler destinations can be linker-assigned|

The64KB BIN's0000..3FFF padding is not runtime RAM. The8KB general-purpose
chip-select window is not evidence of8KB of physical RAM. ROM-visible range
also does not establish every replacement chip's capacity, banking or write
path. The [decode contract](../../docs/analysis/FACTORY_EXTENSION_MEMORY_INTERFACE.md)
records those distinctions.

We will reserve code, calibration, vector, working-state, retained-state and
stack regions centrally. The calibration/code boundary can be ours. Existing
factory routine addresses and ordinary RAM allocations are provenance rather
than mandatory placement. Hardware addresses, actual decode and CPU vectors
remain binding.

A target build needs a selected HC11 toolchain, startup assembly, vector
emission, linker assertions and a checked stack/cycle budget. Host sizes and
pointer widths are not target RAM-use measurements. No binary image or memory
fit is claimed by the present CMake host library.
