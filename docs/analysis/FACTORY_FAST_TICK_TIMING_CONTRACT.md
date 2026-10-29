# Factory fast-tick timing, late entry and compare admission

The previous [current-output witness](FACTORY_INTERRUPT_ADMISSION_AND_CURRENT_OUTPUT.md)
supplied a nested timer IRQ at a selected instruction. This contract adds the
programmed compare interval, conditional instruction-time upper bounds and
counter-driven complete-handler checks. Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Neither the executable image nor the simulator core is changed.

## Interval and explicit premises

7111/7113 writes03 to TMSK2 at3024. Its prescaler field selects16 E cycles
per timer count in the F1-style layout.793D reads the prior OC3 compare at301A;
7940 adds0333=819 and7943 writes it back.7948 clears OC3's20 flag. Thus the
next scheduled comparison is13104 E cycles after the prior comparison, with
16-bit timer wrap. It is based on the previous compare value, not entry time.

The F1 prescaler write has a64-cycle normal reset window. The complete resident
prefix through7113 costs36 nominal E cycles from external-reset handlerFC29
and39 from COP handlerFC1F. It reaches the write within that window under the
nominal reset/bus premise. Later fallbackFC3A requests the same03 value.

Boot's first arm is different:745E..7464 programs current TCNT+8. The819-count
recurrence applies after an OC3 handler advances the compare. It must not be
used to describe that initial eight-count arm.

The generated [cycle bounds](../../maps/structure/factory_tick_cycle_bounds.csv)
use these premises:

- The ordinary path is selected and the stack guard accepts its frame. Factory
  redirection, stack recovery, resets and supplied code are outside the bound.
- ADC is powered, stabilized and uses E clock, as the boot OPTION=B8 requests.
  The four-conversion sequence is ready no later than129 E cycles afterADCTL
  is written. Held-not-ready failure retains the previously documented
  unbounded7B79 wait.
- Instruction costs use nominal HC11 timings. Additional waits and competing
  interrupt work are accounted separately; they are not silently zeroed in
  a whole-machine claim.

Instruction timing comes from [M68HC11ERG](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf),
Table1, pp13..20, cross-checked with [M68HC11RM](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf),
AppendixA. Timer/ADC premises follow [MC68HC11F1](https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf),
sections9.3/10.3, table9-3 and figure10-3. These are a CPU/peripheral contract,
not a new identification or measurement of the installed board.

The numerical comparison uses E cycles and does not require assuming a
crystal frequency in MHz. The actual hardware still must meet the stated
CPU, ADC and bus timing premises.

## A complete busy timer entry has a conditional 1090-cycle envelope

The [timing verifier](../../tools/verify_factory_tick_timing.py) decodes actual
ROM bytes and follows both branch arms with explicit call/return frames. It
allows all local current/IAC decision outcomes. It specializes only the
ordinary accepted-stack prefix and, for the complete busy-handler row, the
existing busy flag. No main controller task is replaced with an estimated cost.

| Scope | Nominal upper E cycles | End convention |
|---|---:|---|
|91A3 IAC step service|118|IncludesRTS|
|F25F bounded ADC helper|173|Includes timeout route andRTS|
|7C13 current calculation|429|IncludesRTS|
|7B6D complete fast service|988|Includes all resident calls andRTS|
|793D through entry to7C13|615|Stops before first current instruction|
|793D through3068 publication|1055|Includes7BA3 store|
|793D through arrival at busy test797D|1060|Stops before that test|
|793D complete busy entry|1090|Includes finalRTI; excludes initial hardware stacking|

These are conservative structural upper bounds, not measured maxima or a
claim that every longest-path branch combination is feasible. In particular,
ADC7's loop is permitted20 poll attempts including the exit attempt: that is
conservative for a129-cycle completion deadline and seven-cycle polling
instruction. F25F permits12 polls; F265 loadsB=12, F26B decrements it and
F26C branches until zero, without another B writer inside the loop. Its
timeout route remains bounded even if that conversion is not ready.

The [per-instruction table](../../maps/structure/factory_tick_instruction_cycles.csv)
retains every included PC, byte encoding and independently assigned nominal
cost. The verifier fails on an unreviewed instruction, call or loop. The
simulator's aggregate cycle counter is not used as timing authority.

## Entry lateness is part of the admission condition

Let:

- **L** be time from the prior OC3 comparison to the first instruction at793D,
  including arbitration and interrupt-entry delay before it.
- **H** be additional interrupt work or extra waiting during that entry, beyond
  the nominal own-instruction envelope.

With an upper bound C for an endpoint, the sufficient exclusion condition is:

```text
L + H + C < 13104
```

For a complete busy entry, C=1090. If **L+H<12014 E cycles**, the handler
returns before its next scheduled compare. A further OC3 entry cannot then
interrupt its current calculation. This is a sufficient bound; exceeding it
does not itself prove that reentry occurs.

For arrival at the busy test the corresponding threshold is12044. Thus the
earlier pre-busy nesting examples also need substantial lateness or competing
work under these premises. An ordinary entry's I=0 instructions alone do not
establish that another compare can arrive in the short prefix.

This does not assign a global L or H bound. A full main pass continues after
797D when not busy and is outside the1090-cycle row. The tail/catch-up has
additional busy-clear/admission windows. The busy-service bound therefore
cannot be promoted into a whole-TOC3 WCET or a universal two-frame nesting
limit. Complete main paths, their masked regions and event-arrival envelopes
still need joining.

## Counter-driven complete-handler examples

The five new [checks](../../tests/test_factory_tick_timing.py) execute the
complete selected busy793D handlers and every resident callee. Their initial
state is the previous current-control fixture: busy004F.2 and current-enable
004C.5 set, reference014D=20, accumulator0150=0400, old error0, B5=40,
batteryA7=128, SP03F4. The stock B2ED selector obtains coefficients64/35.
Four ADC7 samples are zero; ADC4 sample values are explicitly zero too.

The new fixture advances a divide-by16 counter using independently assigned
instruction costs, starts ADC readiness129 cycles after eachADCTL write, and
requests OC3 from compare equality and the enabled pending flag. It applies
the CLI following-instruction delay. No second IRQ is injected at a chosen PC.

Register writes commit at instruction endpoints in this fixture. All selected
rearms remain more than three timer counts from their equality boundary;
high/low-write inhibition and bus phase at a compare-write collision are not
claimed modeled. ADC status is sampled at an instruction boundary. The
example entry times are fixture results under those stated conventions, not
measured board latency or exact board timing tolerance limits.

| First793D instruction lateness L | Next comparison / nested interrupted PC | Final0150 | Words issued to3068, hex |
|---:|---|---:|---|
|12|No second compare before return|1344|0660|
|12425|Compare at13104; nested before7C7D|1344|0654 → 0660|
|12417|Compare at13104; nested before7C96|1344|0654 → 0660|
|12412|Compare at13104; nested before7C99|1489|066A → 0660|
|12358|Compare at13104; nested before7CA5|1489|066A → 0660|

The on-time selected handler uses863 own E cycles, finishing at875 including
its12-cycle initial entry. It does not nest. The late cases rearm from compare
0 to819; their next match is at13104. The nested IRQ starts its793D body at
13116 and rearms to1638. Both frames return intact, no stack recovery occurs,
and busy/pending behavior matches the earlier instruction-order witnesses.

This establishes a counter/ADC-constrained realization **conditional on the
supplied first-entry lateness**. It does not establish that a preceding
ordinary factory path, actual REF/SCI load or hardware fault produces that
lateness. That premise remains an explicit research target. The on-time
exclusion and late-entry realization are different claims.

## Late rearming does not create a queue of elapsed timer intervals

If entry occurs after the next target count has already passed,7943 still
writes old_compare+819. It does not advance to current_TCNT+819 or loop until
the target is in the future. When the equality window has passed, the newly
programmed target is reached again after the counter wraps. A timing model
must preserve that behavior rather than deliver one queued IRQ per elapsed
819-count interval.

A check enters atL=13204, executes the complete busy handler and observes one
3068 write. Compare819 remains programmed after it returns. In counter-only
continuation, the next match is atE=1061680, when TCNT reaches819 after wrap.
COP/reset and other events may intervene on real hardware; the check assigns
them no behavior and makes no claim that the board waits through that span.
Writes during the equality/inhibition border remain separately scoped.

## Independent-reconstruction consequence and remaining target

The fast service is now specified together with an explicit deadline condition.
The current overwrite is excluded for on-time entries satisfying the delay
budget and remains possible in the counter-driven late-entry fixture. Strict
equivalence needs the same distinction; declaring it universally reachable
or universally impossible would each add an unsupported assumption.

The next ROM-only work is to bound masked regions and complete main/tail paths,
then combine them with REF/SCI/other-source admission envelopes. That will
determine which L/H ranges factory execution can reach and the resulting
maximum active nesting/stack footprint. Actual clock, bus and device fault
behavior retain their external evidence boundaries.

## Reproduce

```sh
python tools/verify_factory_tick_timing.py --rom /path/to/BMHM.BIN
python tools/verify_factory_tick_timing.py --check-recorded
python -m unittest discover -s tests -p 'test_factory_tick_timing.py' -v
```

Related: [stack and IAC/gear ordering](FACTORY_STACK_AND_SHARED_OUTPUT_CONTRACT.md),
[ordinary interrupt/X contract](FACTORY_INTERRUPT_ADMISSION_AND_CURRENT_OUTPUT.md),
[scheduler](FACTORY_SCHEDULER_MAP.md), and
[information ledger](FACTORY_EQUIVALENCE_INFORMATION_GAPS.md).
