# Seven-system frozen strategic exam

Each system was evaluated on 5,184 cases. Invalid provider responses count as incorrect. Each GPT-oss-120B case was attempted exactly once.

## Complete-case accuracy

| Section | Marres kernel + adapter | GPT-oss-120B high | TypeSafe Jev | Torchcast 27B | JEV-Gemma4 | Wald one-pass | Drex |
|---|---:|---:|---:|---:|---:|---:|---:|
| best_response | 100.00% | 100.00% | 30.90% | 19.10% | 7.47% | 0.35% | 0.00% |
| strict_dominance | 100.00% | 100.00% | 37.50% | 41.84% | 33.85% | 27.43% | 13.19% |
| pure_nash | 100.00% | 99.83% | 25.87% | 45.66% | 37.33% | 16.67% | 0.17% |
| level_k | 100.00% | 94.21% | 18.46% | 14.70% | 8.04% | 8.48% | 1.85% |

## Individual-answer accuracy

| Section | Marres kernel + adapter | GPT-oss-120B high | TypeSafe Jev | Torchcast 27B | JEV-Gemma4 | Wald one-pass | Drex |
|---|---:|---:|---:|---:|---:|---:|---:|
| best_response | 100.00% | 100.00% | 86.39% | 81.53% | 66.30% | 61.50% | 49.80% |
| strict_dominance | 100.00% | 100.00% | 80.03% | 82.64% | 79.25% | 76.48% | 62.98% |
| pure_nash | 100.00% | 99.96% | 70.70% | 83.72% | 77.43% | 70.31% | 28.52% |
| level_k | 100.00% | 96.27% | 61.65% | 50.25% | 42.76% | 45.92% | 3.09% |

## Execution and limitations

GPT-oss: 5,182 valid, 2 invalid, zero missing. Estimated cumulative cost $6.3782; includes worst-case reservations for unavailable failed-request usage, not an invoice. Pilot cost $0.1306 is separate. Active runtime 91.5 minutes across segments, excluding pauses. Prompt tokens 3,674,804; completion tokens 9,684,926, including 9,405,090 reasoning tokens.

Groq hosted openai/gpt-oss-120b, high reasoning, temperature 0.6, top_p 0.95, seed 20261016, max completion 8192. Same frozen state/questions with a fixed JSON answer instruction. No tools or retries. Two provider JSON-validation failures are retained as incorrect. No failed response was retried or replaced.

GPT-oss is a generative reasoning baseline, not native System One. No probabilities were elicited, so no GPT-oss Brier score. Marres directly encodes these calculations; its result is not full-application or general intelligence validation. Hardware, interfaces and latency differ. Strict ordinal matrices and relabellings are correlated. Pure Nash only; level-k uses declared cardinal spacings and level-0 beliefs. Game154 reconstruction exclusion, logical consistency and per-level diagnostics retained in score JSON. Jev has 29 invalid responses; other six-model details remain in docs/PROTOCOL.md.

Reproduce offline: `python3 reproduce.py`. Normalized predictions are in `results/predictions/`.
