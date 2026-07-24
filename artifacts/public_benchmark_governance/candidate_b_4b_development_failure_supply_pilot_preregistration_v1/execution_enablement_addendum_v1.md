# Execution Enablement Addendum v1

## Status

`RUNNER_ENABLED_NOT_EXECUTED`

本文件是對既有 4B development-only failure-supply pilot **預登錄歷史**的最小範圍補註，**不竄改**原始 `preregistration.md`／`manifest.json` 內容。

## What changed

- 正式 `generate` path 已實作並啟用（crash-safe per-cell journal + atomic persistence + strict resume）。
- Runner 與 targeted mock／zero-model tests 已完成。
- **尚未**呼叫 `qwen3.5:4b`、**尚未**產生任何 200 格正式結果、**尚未**正式評測、**尚未**修改 Healer。

## Protocol pin vs live runtime

- `protocol_ollama_version_pin = 0.32.0`：generation protocol 相容性釘選，**不得**寫成已觀察的實際 runtime。
- 預登錄時曾觀察到本機 Ollama `0.32.1`：僅為歷史觀察，**不得**硬編碼為永久真值。
- 正式執行時必須透過只讀 `/api/tags` + `/api/version` 記錄**當下** `runtime_version`，並與凍結 model tag／完整 digest 核對；任一身分不符即在第一格生成前 fail closed。
- Live metadata check **不得**觸發 generation endpoint。

## Resume (runner-enforced)

Skip 僅在以下全部一致且 `persisted_complete=true`：

cell identity、task ID、seed、condition、model tag、完整 model digest、manifest SHA、prompt SHA、decoding options、runner／protocol identity、非空 raw response、required metadata。

Incomplete／半寫入 journal 不得 skip；可辨識的同格未完成可 quarantine 後重試；identity mismatch 一律 fail closed。

## Next operator step

下一輪仍需人工下達正式 `generate` 命令（含雙重確認旗標與凍結 manifest SHA）。本 addendum 本身不授權自動執行。
