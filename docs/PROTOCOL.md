# Frozen evaluation protocol

## Mathematical conventions

Payoffs are indexed `[row][column][player]`. Player 0 chooses rows, player 1 columns; actions are 0 and 1. Best responses are against each possible pure opponent action. Strict dominance requires strictly better own payoff against both opponent actions. Pure Nash includes empty and multiple-equilibrium sets. No mixed Nash or weak-order game coverage is claimed.

Level-k uses utilities [1,2,3,4], [0,1,2,10] and [0,8,9,10]; both players' level-0 distributions are either uniform or concentrated on the second action. Each player simultaneously best responds to the OTHER player's previous-level distribution. Levels 1–3 are returned for both players; ties within 1e-10 yield equal mixing. These are explicit calculation assumptions, not behavioural observations about real opponents.

## Interfaces and model configurations

Runs dated 16 October 2026, seed 20261016. Every model receives the same mathematical information and question instructions; model-native formatting differs.

| System | Evaluated interface/configuration |
|---|---|
| Marres | Calculation kernel plus exam adapter; proprietary implementation excluded. Saved answers only. |
| TypeSafe Jev | Hosted jev-1.13.0 native typed-decision endpoint; four HTTP workers. |
| Torchcast | torchcast-decision-27b native server, BF16, H100, required fast kernels, 40 CUDA graphs; text-only 8192 context; four clients, serialized server. |
| AutoTrust JEV-Gemma4 | jev-gemma4 alias; BF16, System One LoRA/decision head, default calibration; model-card implementation because referenced engine file was unavailable; nested state formatted as indented JSON; questions scored separately. |
| Wald | wald-v21-none alias, effort none, native one-pass option logits; all answers mode A and zero output tokens; vLLM 0.30.0, Transformers 5.17.0, 8192 context. |
| Drex | drex-dlm native decision server, BF16, H100; four clients, serialized inference. |
| GPT-oss-120B | Groq openai/gpt-oss-120b, high reasoning, parsed reasoning, JSON labels, temperature .6, top_p .95, seed 20261016, max completion 8192; no tools. |

Open-weight runs used pinned model snapshots in the original experiment. Sanitized model configuration metadata is included where available. These facts are recorded experiment configurations, not assertions that current hosted aliases resolve to identical weights. The released generic adapter does not reproduce server provisioning.

GPT-oss completed in three disjoint segments: 3,680 attempts, 1,385 attempts, and 119 attempts. The first two stopped on separate provider JSON-validation errors; only previously unattempted IDs were later submitted. Exactly 5,184 unique IDs, no retries, 5,182 valid responses. Both errors count incorrect. Normalized public files omit raw reasoning and provider transcripts.

## Scoring

Primary: all answers in a case correct. Secondary: individual-answer accuracy. Invalid/missing predictions count incorrect. The scorer withholds an overall equal-section score when valid coverage is incomplete, even if all cases were attempted. For comparisons use section scores with full denominators; do not replace failures with oracle answers.

Native Noul probabilities above .5 predict true; .5 predicts false. Choice labels must maximize reported probabilities; sum residual up to .015 is tolerated and normalization is only for Brier scoring. This rounding tolerance was introduced after the initial Jev pilot; it did not change questions or gold labels. Jev has 29 invalid full-run cases. GPT-oss emits labels only; its probabilities and Brier scores are absent.

The release scorer reports game-154 exclusion sensitivity, per-level accuracy, Nash-count breakdowns, logical consistency and action-relabelling diagnostics. No confidence intervals assuming independent variants are claimed. No prompt tuning or correctness-based retries occurred. Two oracles agree, but both were implemented in the same workflow.

## Reproduction limits

Offline answer and score verification is fully supported. New inference can vary with hardware, numeric precision, hosted revisions and randomness. Native decision-model probabilities and GPT-oss's generated labels are distinct output mechanisms. Costs include different deployment paths; wall-clock times are not hardware-controlled speed benchmarks. Marres source code and raw provider response logs are not included.
