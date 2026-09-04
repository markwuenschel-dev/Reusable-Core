# Real-task manifests

Place real historical or live coding-task manifests here. Each task must include:

- reconstructable task contract
- exact base revision
- exact candidate patch / coding bundle
- independent oracle (`hard_command` + `reference_files`) that checklets never see
- producer and sampling provenance
- `task_origin` of `real_historical` or `real_live`

Ingest with:

```powershell
python -m verification_v1 ingest-fixture-set path/to/manifest-set.json --dataset-out evals/verification_v1/v12/real_dataset.json --freeze
```

Do not copy labels, holdout partitions, or reference oracles into candidate metadata.
