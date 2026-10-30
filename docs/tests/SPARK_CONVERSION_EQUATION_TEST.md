# Spark conversion equation tests

The bounded raw integer contract is now [SPARK_CONVERSION_EQUATION.md](../contracts/SPARK_CONVERSION_EQUATION.md), with the complete derivation in [FACTORY_SPARK_INTEGER_HANDOFF.md](../analysis/FACTORY_SPARK_INTEGER_HANDOFF.md). The earlier opaque `stock_postprocess` equation is superseded by separate saved-timing and period-anchor calculations.

## Independent execution checks

```bash
python tools/verify_factory_spark.py --rom /path/to/BMHM.BIN
python tools/verify_factory_spark.py --check-recorded
python -m unittest discover -s tests -p test_factory_spark.py -v
```

`--rom` verifies the complete stock image identity. The recorded check validates consistency of the committed excerpts and generated maps. The tests execute actual captured instructions on the existing HC11 CPU, independently of the equation implementation and instruction decoder.

| Area | Checked cases |
|---|---|
| `$083F` producer | Every 16-bit period input |
| `$01EA` event decay | Every 16-bit previous value |
| Adaptive update and `$01EC` | 70 boundary combinations and 512 randomized inputs; intermediate write order included |
| `$005F` basis | Eight scale calibrations and seven period boundaries |
| Latency lookup | Every input byte against stock and two alternating-slope tables |
| Startup/sign | Low-byte magnitude, positive/negative words, gain rounding and byte wrap |
| Stack/anchor | Zero/nonzero periods, N-bit selection boundaries, saved byte/word addresses and SP balance |
| Ordered writes | Review vectors and 512 randomized full handoffs |
| Live samples | Separate `$3FF6` and `$01EC` read values at different PCs |
| Admission/init | Boot zero writes, first-reference bypass, count qualification, no-reference timeout |
| External extension | Explicit rejection at `$180F`; effects remain open |

The complete raw-input vectors are `maps/structure/factory_spark_handoff_vectors.csv`. The eight older `tests/static/spark_conversion_vectors.csv` rows check only the assumed `256/90` angle scale and rounded multiply; their obsolete `raw_time_expected` column has been removed.

## Physical validation still needed

Hardware timing, physical angle/count scales, future ASIC readback behavior, word atomicity, interrupt interleavings, the extension implementation, upstream intent construction, and monitoring after `$ABCB` are outside the bounded arithmetic tests. No physical writer is created by these tests.
