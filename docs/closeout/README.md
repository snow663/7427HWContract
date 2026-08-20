# Closeout / Historical Checkpoints

Files in this directory preserve prior audits, planning freezes, implementation checkpoints, and completion snapshots.

They are historical provenance, not the live project-state authority.

For current workstream, current truck calibration, active contracts, supersession rules, and current replacement-OS checkpoint, use:

```text
docs/WORKING_STATE.md
```

Important rule:

```text
historical "current state"
historical "next step"
historical branch status
historical completion percentages
```

must be interpreted as statements true at the time that closeout document was written. They do not override later executable proof, calibration evidence, contracts, investigations, or `docs/WORKING_STATE.md`.

The frozen V1 planning audit remains semantic-design authority where `docs/WORKING_STATE.md` explicitly says it remains frozen; that does not make its old implementation-next-step text current again.

Git history is the archive/version record. Do not duplicate closeout files merely to create a newer numbered snapshot.