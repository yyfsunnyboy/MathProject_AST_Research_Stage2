# 既有600份 development programs：Healer H0/H1 功能評估操作指南

本資產只涵蓋既有60題、300個task-seed identities與P0／Scaffold-like共600份Pipeline-normalized帳。H0沿用既有正式結果；H1固定使用`entrypoint_alias_unique_arity_compatible_v0`。Pipeline extraction與normalization不是Healer。

## 凍結結果

- H0帳：600；H1帳：600。
- H1實際changed：41（P0 39、Scaffold-like 2），全部通過alias-only AST與compile驗證。
- unchanged：559。只有source-state SHA-256精確相同才沿用H0；是否沿用與H0 pass/fail無關。Pipeline無可用輸出的帳以明確canonical unavailable state SHA-256核對，不虛構source bytes。
- 本準備輪沒有呼叫模型、沒有執行EvalPlus、沒有讀取或操作`mbpp_b28`。

## 唯一人工評估指令

請在repository根目錄的WSL shell中執行以下唯一一條指令；不得改變manifest、hash、interpreter、`--parallel 1`或output path：

```bash
/home/yehya/.venvs/ast_evalplus/bin/python scripts/run_mbpp_existing600_healer_eval.py --manifest artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/manifest.json --manifest-sha256 420eb05267f11f4f9f157f63167398e86fbc68322f33b33b9bf5656fb6f24913 --parallel 1 --output-dir artifacts/public_benchmark_governance/healer_h0_h1_functional_evaluation_v1/manual_evalplus_run_001
```

Driver只評估41個changed H1 cells，拒絕其他Healer／Pipeline、identity、數量、parallel值、既有output directory與任何hash drift；它沒有generation、retry、resume、selective acceptance或overwrite功能。559格不會重新執行EvalPlus，也不會覆寫H0。

評估完成只會產出changed-H1原始結果，不會先宣告rescue或regression。之後必須另行、明確執行paired analyzer，才可依預先固定規則分類fail→fail、fail→pass、pass→fail、pass→pass，並分層列出P0與Scaffold-like。

判定固定為：regression > 0不合格；regression = 0且rescue >= 1才可進入獨立prospective qualification；兩者皆0則僅能稱靜態安全且未觀察到功能效益。不得依結果撤回個別transformation。
