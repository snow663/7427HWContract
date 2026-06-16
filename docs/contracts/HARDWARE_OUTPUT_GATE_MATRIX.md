# Hardware Output Gate Matrix

            Purpose: record the current route, preservation status, bench status, implementation permission, blocked conditions, and next required proof for each hard hardware-output subsystem.

            This is a planning/static-gate artifact only. It does not implement runtime ASM, does not create a hardware writer, does not record bench results, and does not relax any existing engine-runnable gate.

            ## Repo-wide rule

            ```text
            Preserve complete stock hardware driver:
              static-proof route possible

            Write hardware directly/custom:
              bench-proof route required
            ```

            ## Current route stack

            ```text
            Spark:
              stock handoff preservation accepted as the working route
              custom direct spark writer remains bench-required
              physical ASIC spark semantics deferred

            Fuel:
              stock output-driver preservation considered
              decision = incomplete_continue_3FCE_bench_route
              compact $3FCE SLICE-0 bench path remains active
              SLICE-1 still blocked by FUEL-001 through FUEL-004

            IAC:
              stock driver preservation contract defined
              preservation proof not complete
              custom direct A/B/Enable/park writer remains bench-required
            ```

            ## Gate matrix

            | row_id | subsystem | current route | decision state | next required proof |
            |---|---|---|---|---|
            | `fuel_compact_3FCE` | fuel | active compact direct $3FCE SLICE-0 bench route | active_bench_route | run local verifiers, bench fixed vectors, enter measured evidence, keep FUEL-004 not_run until real dropout/unsafe path is invoked |
| `fuel_stock_output_driver` | fuel | candidate preserved stock fuel scheduler/output-driver route | candidate_incomplete | complete stock fuel driver static proof index to accepted_static_route or reject and continue $3FCE bench route |
| `spark_stock_handoff` | spark | accepted preserved stock ASIC handoff route | accepted_static_route | pin complete preserved stock handoff routine range, inputs, state seeding, side effects, and no alternate direct writer |
| `spark_custom_writer` | spark | custom direct ASIC spark writer | blocked_bench_required | only possible after explicit bench proof of ASIC-facing spark semantics and safe first-event/dropout behavior |
| `iac_stock_driver` | iac | candidate preserved stock IAC output-driver route | contract_defined_not_proven | complete IAC stock-driver static proof index or bench-prove a custom A/B/Enable/park writer |
| `iac_custom_writer` | iac | custom direct A/B/Enable/park writer | blocked_bench_required | bench-prove physical A/B/Enable/phase/park behavior, including reset/park/dropout safety |

            ## Hard decisions

            ```text
            fuel_compact_3FCE:
              active_bench_route
              FUEL-001 through FUEL-004 still gate SLICE-1

            fuel_stock_output_driver:
              candidate_incomplete
              cannot supersede compact $3FCE bench path yet

            spark_stock_handoff:
              accepted_static_route
              clean spark state may feed preserved stock handoff after static completeness proof

            spark_custom_writer:
              blocked_bench_required

            iac_stock_driver:
              contract_defined_not_proven
              cannot bypass IAC bench proof yet

            iac_custom_writer:
              blocked_bench_required
            ```

            ## Non-relaxation clauses

            ```text
            This matrix does not make SLICE-1 legal.
            This matrix does not mark FUEL-001 through FUEL-004 passed.
            This matrix does not accept fuel stock-driver preservation.
            This matrix does not accept IAC stock-driver preservation.
            This matrix does not permit a custom direct spark writer.
            This matrix does not permit a custom direct IAC writer.
            This matrix does not create any runtime ASM.
            ```
