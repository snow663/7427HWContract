# STATIC_ARTIFACT_BUILDER_VERIFICATION

## Purpose

Verify that committed static-artifact builder scripts reproduce their committed CSV/Markdown/test outputs.

This is an internal repo consistency check only.

It does not:

```text
prove hardware behavior
change subsystem gate decisions
mark bench proofs passed
accept fuel stock-driver preservation
accept IAC stock-driver preservation
relax SLICE-1
create runtime ASM
create hardware writers
```

## Files

```text
tools/verify_static_artifact_builders.py
maps/tests/static_artifact_builder_verification.csv
docs/tests/STATIC_ARTIFACT_BUILDER_VERIFICATION.md
```

## Command

From repo root:

```bash
python tools/verify_static_artifact_builders.py
```

To write a machine-readable report:

```bash
python tools/verify_static_artifact_builders.py --write-report
```

Default report path:

```text
maps/tests/static_artifact_builder_verification.csv
```

## Verification model

The verifier:

```text
1. Discovers every committed tools/build_*.py builder.
2. Copies the repository into a temporary directory.
3. Runs each builder inside its own temporary repo copy.
4. Compares the post-build temp tree against the committed repo tree.
5. Reports any changed, missing, extra, or mismatched files.
6. Treats mismatches as repo defects, not hardware findings.
```

The production working tree is not used as the build target. Builders run in temp copies so normal verification should not mutate source files.

## Pass criteria

```text
Every discovered builder exits with return code 0.
No committed output differs after builder execution in the temp copy.
No builder creates uncommitted output files.
No builder deletes committed output files.
```

Expected terminal summary:

```text
PASS: <N> static artifact builder(s) reproduce committed artifacts
```

## Fail criteria

Any of the following fails the verification:

```text
builder timeout
builder nonzero return code
generated file differs from committed file
builder creates file absent from repo
builder deletes committed file
```

Failures indicate repo artifact drift. They do not indicate hardware behavior.

## Gate non-relaxation

Running this verifier must not change these decisions:

```text
fuel_compact_3FCE:
  remains active_bench_route

fuel_stock_output_driver:
  remains incomplete_continue_3FCE_bench_route unless separately updated by a valid static proof artifact

spark_stock_handoff:
  remains accepted_static_route

spark_custom_writer:
  remains blocked_bench_required

iac_stock_driver:
  remains contract_defined_not_proven unless separately updated by a valid static proof artifact

iac_custom_writer:
  remains blocked_bench_required
```

## Result interpretation

```text
verifier PASS:
  static builders reproduce committed static artifacts

verifier FAIL:
  one or more static artifacts are stale, missing, extra, or generated differently

verifier PASS does not mean:
  hardware proof passed
  bench proof passed
  SLICE-1 is allowed
  custom hardware writers are allowed
```

## Required repair path if failed

```text
1. Inspect the failing builder and reported changed/missing/extra files.
2. Decide whether the builder or committed output is authoritative.
3. Update only the stale static artifact or the builder.
4. Re-run the verifier.
5. Do not change hardware gate decisions as part of repair unless a separate proof artifact justifies it.
```
