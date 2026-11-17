# Foreground refresh and stack-watermark contract

The stock BMHM bytes remain the authority (SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`).

| Entry | Source | Behavior |
|---|---|---|
| `pcm_ram_refresh` |746C..74B2|Request admission; eight word self-copies per masked block; cursor progression and completion.|
| `pcm_stack_watermark` |74B4..74CF|Scan the supplied logical CPU stack and update its minimum first-used address.|
| `pcm_background_pass` |746C..74D0|Refresh, literal CLI, watermark, then an explicit WAI boundary.|
| `pcm_reset_timers` |7459..746B|Clear all TFLG1 flags before the first TCNT-relative timer arm.|

The existing reset sequence now calls `pcm_reset_timers`; it previously skipped
7459..745D's flag acknowledgment. The existing `pcm_timer_arm` remains the
745E..746B primitive, preserving its callers and calibrated first-compare count.

Refresh reads0051.2 once on admission and captures cursor029B. Normal resident
starts are aligned16-byte cursors0000..0400 and0800..0900. At0400 it redirects
to0800, publishing the redirect before masking. At0900 it ends the pass. This
rooted producer contract does not imply a whitelist or safe bounds for a
corrupted cursor; no invented address clamp or iteration limit is added.

Each block executes a literal SEI, eight adjacent word reads and unchanged
word writes, a16-byte cursor advance/store and a literal CLI. Actual74A4 bytes
are `C6 10`, so the increment is16 despite ambiguous inherited decimal text.
The word value is captured before its write; provider mutation between them
does not change that captured value. The local cursor survives callback activity
at CLI. The entire pass is not a single critical section.

Completion executes a **byte** clear at029B, followed by a fresh0051 RMW that
clears only bit04. A separately changed029C low byte or unrelated0051 bits
survive. Cursor and watermark are canonical `PcmSystem` fields, at logical
029B and02D1. Providers must bind all self-copy RAM words to the existing named
owners, including serial words, and preserve word callback width/order.

The stack scanner reads03B0..03FF until the first nonzero byte or the upper
bound. Even an all-zero window ends at03FF. It reads02D1 once for the zero
test and, if nonzero, reads it again for CPX. It writes the captured scan address
only when the first read was zero or the address is below the second read.
It is a minimum address, not a count of unused bytes.

`pcm_background_pass` returns appended status9,
`PCM_BACKGROUND_WAIT_BOUNDARY`, before74D0 executes WAI. WAI's interrupt frame,
wake/RTI and74D1's resume branch require the target ABI; no native host C stack
is passed off as that CPU stack. A host driver resumes another foreground pass
after supplying the appropriate logical-stack state.

Focused verification passes **1,035 C/ROM comparisons**, covering **all52
resident starts** at7459..74CF. Cases cover all resident cursor starts, each
possible first-used stack byte, captured-word and minimum-word mutation, a
pending ordinary IRQ deferred to CLI, terminal byte/flag preservation, first
timer wrap and all provider/mask failed prefixes of selected paths. Complete
refresh passes also have selected early/middle/late failures.

Slot-F request, slot-E late latch and foreground completion share canonical
state in a joined fixture. The unported slot-F callees are an explicit supplied
binding. Its synthetic RTS sentinel is removed before supplying the common
foreground logical-stack snapshot. Existing reset-serial/BLM seeds join the
new timer and background bodies; prior callee frame bytes03F0..03FF are excluded
only in those joined fixture modes. Standalone refresh/watermark cases observe
the whole logical stack window as data. This is not a target call-stack proof.

The kernel/hardware smoke contracts pass. Full repository regression remains
deferred until the requested "pull and merge" step.
