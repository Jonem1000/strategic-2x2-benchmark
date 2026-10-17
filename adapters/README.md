# Optional inference adapter

`run.py` provides a portable interface for new evaluations. It has passed simulated HTTP administration tests; live inference has not been validated for this utility. Archived results were produced by model-specific runners, so identical inference outputs are not guaranteed.

- `--mode native`: sends unchanged frozen state/questions plus a requested model ID to a native `/v1/systemone` server. Parses probability-bearing Noul/choice responses through the shared strict parser. Appropriate only after verifying a server contract; it does not install or implement any model server. Local loopback is default.
- `--mode groq`: wraps identical frozen state/questions in the original fixed instruction and requests generated Boolean/choice JSON labels. Default high reasoning, 8192 maximum completion tokens, temperature 0.6, top_p 0.95, fixed seed. Does not invent probabilities. A Groq key is read from `GROQ_API_KEY` only when execution is enabled.

Dry run is default; it makes no network calls and requires no key. `--execute --out runs/new-pilot` enables the 108-case pilot. `--full` selects all 5,184 cases. Fresh output paths must not exist; explicit `--resume` continues only unattempted cases. No retry or answer-key access; first error stops the run. The caller is responsible for provider rates and spending limits; this portable utility has no dollar cap. Full runs can incur charges. Never commit new raw results without reviewing them for private metadata and redistribution rights.

Examples (dry runs):

```sh
python3 adapters/run.py --mode groq --model openai/gpt-oss-120b
python3 adapters/run.py --mode native --model torchcast-decision-27b
python3 adapters/run.py --mode native --model wald-v21-none --effort none
```

Hosted native endpoints require an explicitly supplied HTTPS URL and `--key-env VARIABLE_NAME`. Do not put a secret in a command argument or URL. No default endpoint is assumed for TypeSafe Jev. AutoTrust Gemma and Drex require their specific server implementations; identical route names do not establish compatibility.

## Machine administration contract

Start with `benchmark.json` in the full repository. JSON Schemas live in `schemas/`; record each schema/version with the run. Schemas describe structure, while the runtime additionally checks frozen byte hashes, unique case IDs, exact answer IDs, model identity, finite probabilities, probability sums, and choice maxima. `noul` means a Boolean judgement: native probability strictly above 0.5 maps to true (0.5 maps to false). Choice labels are exactly `first`, `second`, and `equal`. Native sums tolerate rounding by 0.0150001; normalized probabilities are used for Brier scores. Generated labels have no calibration probabilities.

The supported runner platform is Python 3.10+ on macOS/Linux (POSIX file locking). The runner imports only `contracts.py`, not the answer key or mathematical oracle.

```sh
# From the full repository: validate, run, and score a pilot.
python3 administer.py verify
python3 administer.py run --mode native --model MODEL --execute --out runs/pilot
# Continue only cases never attempted, retaining failed cases as incorrect.
python3 administer.py run --mode native --model MODEL --execute --out runs/pilot --resume
# Export an isolated inference-side package; destination must not exist.
python3 administer.py export --out /tmp/questions-only
```

`administer.py run` invokes the adapter, which validates frozen inputs before dispatch, then scores available predictions offline. Full-repository scoring uses the pilot denominator by default and all 5,184 cases with `--full`. The export runs `adapters/run.py` directly and returns its run directory to the administrator for grading. Exported files contain no keys, oracle implementation, catalogue metadata, saved model results, or answer key. Public availability of this exam still permits contamination.

Execution writes `manifest.json`, durable per-case `records/`, normalized `predictions.jsonl`, and `execution.json`. Status is `partial`, `complete`, or `complete_with_errors`; counts distinguish attempted, valid, failed, and remaining. Exit 0 means every selected case produced a valid response, **not that its answers are correct**. Inference failure or incomplete coverage exits 1; argument errors exit 2; unexpected failures also exit nonzero. Dry runs exit 0 without claiming execution.

Fresh execution requires a new output directory. Resume requires the same mode, model, endpoint, frozen input hashes, code hashes, selection and model configuration. A per-run exclusive lock prevents concurrent dispatch. A durable `dispatching` record is committed before HTTP. After interruption, that case is marked indeterminate and never resent; it counts incorrect. This is conservative at-most-once dispatch, not provider-level exactly-once execution: a crash before transmission can consume a case without sending it. Stop-on-first-error remains the default; `--resume` advances only to unattempted cases. Never delete or edit ledger files to retry. Completed raw responses are reparsed on resume. Retain an immutable copy of the run for auditing.

No automatic rate-limit retry, GPU provisioning, cost accounting or budget enforcement is supplied. The default interval is 2.1 seconds after each successful call (`--interval`), with a 180-second HTTP timeout. Timeouts may still incur provider charges. Configure provider-side spending limits before paid execution. Model-specific server installation and native API compatibility must be established separately; this utility has been tested against simulated HTTP servers, not newly validated against each live model.
