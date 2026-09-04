# VS-V1.2 evaluation artifacts

- `vs-v1.1-baseline-001.json` — frozen V1.1 implementation identity.
- `vs-v1.1-baseline-001.sources.json` — content-addressed source snapshot; reconstructs the V1.1 files without Git.
- `metric_integrity_dataset.json` — hand-computed metric fixture used by unit tests and CI.
- `pilot_dataset.json` — frozen ingestion of the V1.1 engineering fixture set (`task_origin=engineering_fixture`). Not a real-task prevalence sample.

Real historical/live tasks belong in `real_tasks/` with explicit provenance. Do not mix them with engineering fixtures when reporting prevalence.
