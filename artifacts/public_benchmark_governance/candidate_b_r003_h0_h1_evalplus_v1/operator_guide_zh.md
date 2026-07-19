# Candidate B r003：H0/H1 凍結與 EvalPlus 執行準備操作指南

本輪只凍結 `mbpp_q35_9b_candidate_b_development60_replay_r003` 的300個完整 journal，重建 Candidate B H0/H1 帳目，並準備 fail-closed EvalPlus 輸入。禁止呼叫模型、禁止修改 prompt／Pipeline／Healer、禁止 resume／retry／覆寫 r003、禁止使用 r001／r002 response。

## 凍結結果

- Candidate B programs：300；H0/H1 accounts：600。
- H1 transformed（changed）：2；unchanged：298（H1 必須與 H0 byte-identical）。
- 待執行 EvalPlus cells：302（Candidate B H0 全300 + changed H1 2）。
- unchanged H1 只能在對應 H0 EvalPlus 結果存在且 identity／source SHA-256 完全一致時重用。
- P0-H0／P0-H1 既有各300帳維持 identity-hash 沿用，形成後續完整2×2（600 programs／1200 accounts）；本輪不做 paired outcome analysis。
- model_calls=0；evalplus_executions=0；正式 EvalPlus output directory 尚未建立。

## 唯一人工 WSL EvalPlus 指令

請在 repository 根目錄的 WSL shell 執行以下唯一一條指令；不得改變 interpreter、manifest、hash、`--parallel 1` 或 output path：

```bash
/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_candidate_b_r003_evalplus.py --manifest artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manifest.json --manifest-sha256 6a84a328307f3ce98a49933008aa18da481aae52920238b9204dcf47b1280606 --parallel 1 --output-dir artifacts/public_benchmark_governance/candidate_b_r003_h0_h1_evalplus_v1/manual_evalplus_run_001
```

Driver 只評估上述 302 格，拒絕 hash drift、identity mismatch、duplicate／missing、既有 output directory、Windows 本機執行與任何 generation／retry／resume／overwrite 路徑。評估完成後才可另行授權 paired analysis；本指南不判定 Candidate B gate。
