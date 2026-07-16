# Public Benchmark Generation Protocol v1 Summary

- Frozen date: 2026-07-16
- Protocol version: `generation_protocol_v1`
- Ollama version: `0.32.0`
- API endpoint: `/api/chat`
- No-thinking control: structured request field `think=false`
- `/nothink` string: not used

## Frozen Models

| Role | Tag | Digest | Size (bytes) | Parameters | Quantization | Modified time | Public benchmark use |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| Primary development | `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 6594474711 | 9.7B | Q4_K_M | 2026-07-16T22:38:34.436418+08:00 | Allowed by this protocol |
| Frozen transfer | `qwen3.5:4b` | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` | 3389983735 | 4.7B | Q4_K_M | 2026-07-16T22:38:31.4275049+08:00 | Forbidden; transfer-only |

Both `/api/show` templates were `{{ .Prompt }}` with SHA-256
`b507b9c2f6ca642bffcd06665ea7c91f235fd32daeefdf875a0f938db05fb315`.
Neither template contains `/nothink`; no-thinking is therefore controlled and
audited through the structured Ollama API field.

## Generation Parameters

- `thinking=false`
- `temperature=0.2`
- `top_p=0.95`
- `top_k=20`
- `num_ctx=8192`
- `num_predict=2048`
- `samples_per_task=5`
- `seeds=[11,22,33,44,55]`
- `stream=false`

The runner pairs baseline and Scaffold arms by task and seed. It preserves the
request payload, raw response, and response metadata; protocol runs reject
resume, automatic retry, model overrides, and non-empty output directories.
Raw and Healed analyses must share the same saved original output. Evaluator
feedback is not supplied to the model, and the Healer remains evaluator-blind.

## Synthetic No-Thinking Probes

The prompt was synthetic and contained no public benchmark task content. Each
model was called exactly once with the frozen sampling parameters and explicit
`think=false`.

| Model | HTTP | Response | Thinking content | Think tags | Metadata/raw body |
| --- | ---: | --- | --- | --- | --- |
| `qwen3.5:9b` | 200 | `PROTOCOL_OK` | None | None | Complete and saved |
| `qwen3.5:4b` | 200 | `PROTOCOL_OK` | None | None | Complete and saved |

The 4B call was only this synthetic transfer-model probe. No HumanEval+ or
MBPP+ task was executed. Full requests, raw response bodies, and generation
metadata are recorded in `synthetic_probe_manifest.json`.
