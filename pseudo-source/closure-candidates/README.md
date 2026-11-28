# Resident closure candidates — batch 1

Isolated host-C translations for seven unresolved entries in the published
436-routine development census. The exact ROM authority is the committed
BMHM byte evidence (SHA-256 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004).
Use the existing factory instruction interpreter and logical RAM fixture to
compare return channels, complete retained RAM snapshots and ordered provider
writes, including injected write failures. The shared CPU, private HC11 stack,
fixed read fixtures and absence of asynchronous interleaving limit the claim.
No native compiler or direct flashable image is involved.

```sh
cmake -S pseudo-source/closure-candidates -B /tmp/7427-closure -DCMAKE_BUILD_TYPE=
cmake --build /tmp/7427-closure --parallel 2
python3 pseudo-source/closure-candidates/compare_batch1.py /tmp/7427-closure/pcm_closure_batch1
```

The new functions are not yet bound into AE85 or the canonical source index.
Do not decrement the implementation census until integration and regeneration.
The candidate tests must pass at the exact reviewed head before integrating.

## Batch 1 verified; batch 2 staged

PR #54 exact head `29e7b8e` passed 5,351 comparisons, 106/106 local instruction
starts and 34/34 conditional outcomes (run 46140522005). It was merged as
`aeaa3c0`; canonical source/index integration remains pending.

Batch 2 adds E7C7, E808, E847, E8C8, EB81, EBC0, ECCC and EF2B. Replay
`python3 pseudo-source/closure-candidates/compare_batch2.py /tmp/7427-closure/pcm_closure_batch1`.
The code 72 magnitude operation preserves the literal NEGB/NEGA/SBCA sequence,
including its low-byte-zero behavior; do not normalize it to conventional abs.
No batch 2 pass or canonical mapping is claimed until the gate succeeds.
