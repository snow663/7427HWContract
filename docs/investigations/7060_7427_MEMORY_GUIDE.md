# How the 7060 and 7427 use memory

At startup, the firmware tells the CPU which addresses should activate each chip-select signal. **CS** means *chip select*. **EN** means *enable*. When the CPU reads or writes an address, this setup helps determine which device answers.

## Where the extra 16 KiB came from

Follow address **$4000**. On the stock 7060 running BAMW, reading it samples a board port. On the stock 7427 running BMHM, reading it fetches a byte from the firmware image. The 7427 reaches its corresponding board port at **$3060**. Its image therefore starts at $4000 and extends to $FFFF (48 KiB). The 7060 image starts at $8000 and extends to $FFFF (32 KiB). The extra room for code and calibration is **$4000–$7FFF**.

| If the firmware wants to… | 7060 BAMW | 7427 BMHM |
|---|---|---|
| Talk to the CPU's own timer or serial registers | Register block starts at $1000 | Register block starts at $3000 after startup |
| Read the board's Port C inputs | Read $4004 using the general select | Read $3064 using I/O select 1 |
| Send a byte to board Port B | Write $4002 using the general select | Write $3062 using I/O select 1 |
| Reach the event hardware at $3FCE | Firmware writes here; the board signal that enables it is still open | Address falls under I/O select 2 |

## Why a RAM address appears alongside a port address

On the 7427, the instruction at **$F414** reads the switches on port **$3064**. The next instruction, at **$F417**, saves that byte in RAM at **$004D**. Later code can read $004D to see what the switches looked like when sampled. That saved copy is an **input shadow**. The 7060 does the same job with $4004 and $0071.

An **output shadow** goes the other way. On the 7427, code prepares the desired Port B bits in $004C. The output routine copies that byte to $3062. This lets several routines update their own bits before one routine writes the port. Both examples involve explicit copy instructions. Whether two addresses can reach the same physical memory cell is a separate board-decoding question.

## What needs to survive, and for how long?

| Kind of RAM use | Example | Why the firmware keeps it |
|---|---|---|
| Calculation scratch | 7427 $0871–$0872 | The idle routine saves a two-byte value and adds it into a calculation a few instructions later. Other code also writes this location. |
| State between operations | 7060 $016B | The next throttle calculation needs the previous throttle sample to detect a change. |
| Learned fuel trim | 7060 $0232–$0241 (16 cells); 7427 $02B3–$02C7 (21 cells) | The controller keeps fuel corrections for different operating conditions. The 7427 startup recovery path resets its cells to $80 when retained-state validation fails. |
| Separately checked adaptive memory | 7427 $02F8–$032B (52 bytes) | Startup checks this bank separately and fills it with $80 if the check fails. |

The startup code tells us which learned values GM expected to reuse on the next start. The electrical question of how long those bytes survive with power removed is still open.

## How to use the access list

Open the CSV and filter **stock_image** to BMHM, then **instruction_pc** to F414. The row says CSIO1, R, 3064. In ordinary language, the instruction stored at $F414 reads one byte from the board at $3064. Change the PC filter to F417 and the row says Internal RAM, W, 004D. Together those rows show the input shadow being made. RW denotes an instruction that both reads and writes its operand. The BAMW list covers selected hardware paths, so missing rows there are inconclusive.

[Open the instruction ledger](../../maps/structure/7060_7427_select_accesses.csv) · [See the startup register values and detailed evidence](BAMW_BMHM_SELECT_AND_RAM.md)
