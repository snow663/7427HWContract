# 7427 Stock ALDL / SCI Handshake

## Scope

This document freezes the software-facing serial behavior proven from the `$31` BMHM executable before the replacement OS begins using the external ALDL line.

The goal is to preserve the stock SCI/transceiver handoff without assigning an incorrect meaning to neighboring `$3FFC/$3FFD` bits.

## HC11 SCI register placement

The stock reset code relocates the HC11 register block from `$1000` to `$3000`.

Stock `LCC7C` initializes the SCI baud register:

```text
$302B = $04
```

The retained serial register addresses are therefore:

```text
$302B  BAUD
$302C  SCCR1
$302D  SCCR2
$302E  SCSR
$302F  SCDR
```

## Stock transmit-start sequence

At `F637-F645`, stock BMHM performs:

```text
LDD  $3FFC
JSR  LF3ED          ; stock very-short access delay
ORAB #$04
STD  $3FFC
CLI
LDAA #$88
STAA $302D
```

Because `LDD` loads `$3FFC` into A and `$3FFD` into B, `ORAB #$04` changes **bit 2 of the low byte at `$3FFD`**, not bit 2 of `$3FFC`.

`$302D = $88` enables the stock SCI transmit path (`TIE + TE`).

## Stock byte transmit

The SCI interrupt handler begins at `F7EA`.

Its transmit branch checks:

```text
SCCR2 bit 7  ; transmit interrupt enabled
SCSR  bit 7  ; transmit data register empty
```

and then calls `LF822`.

`LF822` ultimately writes each outgoing byte at `F8E6`:

```text
STAA $302F
```

The stock message checksum is accumulated while bytes are transmitted.

## Stock transmit-complete handoff

After the message has been exhausted, stock changes SCCR2 to:

```text
$302D = $40
```

so the SCI interrupt path waits for transmit-complete rather than another empty transmit-data-register event.

At `F807-F81B`, the SCI ISR verifies the transmit-complete condition, returns the SCI toward receive operation, and releases the external ALDL driver:

```text
LDAA #$26
STAA $302D

LDD  $3FFC
JSR  LF3ED
ANDB #$FB
STD  $3FFC
```

Again, `ANDB #$FB` clears **bit 2 of `$3FFD`**.

## Critical distinction from asynchronous fuel

The asynchronous-fuel command island also performs a bit-2 edge within the `$3FFC/$3FFD` 16-bit register pair, but it operates on the **high byte**:

```text
LDD  $3FFC
ANDA #$FB
STD  $3FFC
ORAA #$04
STD  $3FFC
```

Therefore:

```text
ALDL transceiver control     = low byte  $3FFD bit 2  (B register)
async-fuel trigger control   = high byte $3FFC bit 2  (A register)
```

These are distinct software-facing hardware controls and must never be collapsed into one symbolic bit.

## Replacement-OS rule

The ALDL HAL may preserve the stock 16-bit read/modify/write access sequence and `LF3ED` call-delay behavior, but it must modify only the low-byte `$3FFD` bit-2 state for serial-driver control.

The asynchronous-fuel HAL continues to own the high-byte `$3FFC` bit-2 trigger.

The first ALDL bring-up image remains engine-off and must not enable fuel, spark, IAC, pump, or other actuator authority.
