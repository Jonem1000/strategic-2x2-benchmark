# Validation

## Data and scores

- All frozen data files match their recorded SHA-256 hashes.
- All 29,952 reference answers agree with both oracle implementations.
- Oracle, parser, scoring and administration tests pass.
- Normalized predictions reproduce all seven saved score files exactly.

## Adapter checks

Both inference modes pass dry-run and local simulated-HTTP checks. Tests cover failures, durable resume, interrupted dispatch, configuration changes, input tampering, exclusive locking, raw-response reparsing, isolated questions-only exports, and a complete 108-case simulated pilot through the run-and-score command. The generated-label parser rejects duplicate JSON keys and nonfinite values. The portable adapter has not been live-tested; archived inference used model-specific runners.

## Package contents

The package excludes credentials, personal filesystem paths, rental infrastructure records, raw reasoning transcripts, model weights and proprietary Marres code. A text-pattern scan found no recognizable credential strings or private-key blocks. This check is not a comprehensive security audit.

## Reproduce

```sh
python3 reproduce.py
python3 -m unittest -v
```

These checks require Python 3.10+ and no external network access. Administration tests bind a loopback HTTP server.
