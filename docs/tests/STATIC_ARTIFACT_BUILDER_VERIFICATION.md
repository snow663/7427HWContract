# STATIC_ARTIFACT_BUILDER_VERIFICATION

## Purpose

Verify that committed static-artifact builder scripts reproduce their committed CSV/Markdown/test outputs without falsely failing builders that require explicit CLI arguments.

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
2. Checks whether the builder can be invoked safely as a zero-argument builder.
3. Skips parameterized builders that need explicit CLI arguments unless they are listed in the manifest.
4. Skips builders whose --help path fails without a manifest entry, including optional-dependency builders.
5. Copies the repository into a temporary directory.
6. Runs each runnable builder inside its own temporary repo copy.
7. Compares the post-build temp tree against the committed repo tree.
8. Reports changed, missing, extra, or mismatched files.
9. Treats mismatches as repo defects, not hardware findings.
```

The production working tree is not used as the build target. Builders run in temp copies so normal verification should not mutate source files.

## Manifest rule

Some builders are intentionally parameterized and require arguments such as:

```text
--out-md
--out-csv
--name
--addr
--watch
--start-pc
--end-pc
--vectors
--subsystem
```

Those builders must not be run with guessed arguments. They are skipped unless `BUILDER_INVOCATION_MANIFEST` in `tools/verify_static_artifact_builders.py` defines their canonical invocation.

A skipped parameterized builder is not a hardware pass and not a builder-output pass. It means only:

```text
the verifier did not have a canonical invocation for this builder
```

## Pass criteria

```text
All runnable zero-argument builders exit with return code 0.
All manifest-driven builders exit with return code 0.
No runnable builder changes committed output in the temp copy.
No runnable builder creates uncommitted output files.
No runnable builder deletes committed output files.
Parameterized builders without manifest entries are reported as skips, not failures.
```

Expected terminal summary when no runnable-builder failures exist:

```text
PASS: static builder verification completed with no runnable-builder failures
```

## Fail criteria

Any of the following fails the verification for a runnable builder:

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
verifier runnable-builder PASS:
  runnable static builders reproduce committed static artifacts

verifier SKIP:
  builder requires manifest/canonical arguments or optional dependency handling

verifier FAIL:
  one or more runnable static artifacts are stale, missing, extra, or generated differently

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
4. Add manifest entries only when the canonical invocation is known.
5. Re-run the verifier.
6. Do not change hardware gate decisions as part of repair unless a separate proof artifact justifies it.
```
