# Optional inference adapter

`run.py` provides a portable interface for new evaluations. It has passed offline dry-run checks; live inference has not been validated for this utility. Archived results were produced by model-specific runners, so identical inference outputs are not guaranteed.

- `--mode native`: sends unchanged frozen state/questions plus a requested model ID to a native `/v1/systemone` server. Parses probability-bearing Noul/choice responses through the original strict parser. Appropriate only after verifying a server contract; it does not install or implement any model server. Local loopback is default.
- `--mode groq`: wraps identical frozen state/questions in the original fixed instruction and requests generated Boolean/choice JSON labels. Default high reasoning, 8192 maximum completion tokens, temperature 0.6, top_p 0.95, fixed seed. Does not invent probabilities. A Groq key is read from `GROQ_API_KEY` only when execution is enabled.

Dry run is default; it makes no network calls and requires no key. `--execute --out runs/new-pilot` enables the 108-case pilot. `--full` selects all 5,184 cases. Output paths must not exist. No retry or answer-key access; first error stops the run. The caller is responsible for provider rates and spending limits; this portable utility has no dollar cap. Full runs can incur charges. Never commit new raw results without reviewing them for private metadata and redistribution rights.

Examples (dry runs):

```sh
python3 adapters/run.py --mode groq --model openai/gpt-oss-120b
python3 adapters/run.py --mode native --model torchcast-decision-27b
python3 adapters/run.py --mode native --model wald-v21-none --effort none
```

Hosted native endpoints require an explicitly supplied HTTPS URL and `--key-env VARIABLE_NAME`. Do not put a secret in a command argument or URL. No default endpoint is assumed for TypeSafe Jev. AutoTrust Gemma and Drex require their specific server implementations; identical route names do not establish compatibility.
