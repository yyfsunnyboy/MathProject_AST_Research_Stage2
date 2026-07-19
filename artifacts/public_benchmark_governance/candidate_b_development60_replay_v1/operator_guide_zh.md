# Candidate B：既有60題 development 統一 replay 操作指南

此規格是development replay，不是validation或confirmatory evidence。P0的300份raw及600個H0/H1結果只按identity與SHA-256沿用；不得重新生成或重跑EvalPlus。Candidate B只生成300份raw，H0/H1共享同一raw與Pipeline輸入。

Candidate B文字SHA-256：`bd91435816a1aa89afa23f1a1c0f3dc60f5890abfae9acaea6496db4441fb719`。Healer固定為`entrypoint_alias_unique_arity_compatible_v0`。Pipeline correction不屬於Healer。

Runner禁止resume、retry、選擇性補跑與overwrite；每格只嘗試一次並以同目錄temporary file、flush、fsync、atomic rename及read-back hash保存journal。300格未全部完成時，不建立aggregate raw、Pipeline或H0/H1帳。Runner不含EvalPlus功能。

首次人工啟動在建立run directory與任何generation cell之前，因舊版provenance helper未讀取`/api/tags models[].details.quantization_level`而fail-closed。實際API值為字串`Q4_K_M`；舊helper回傳Python `None`。該次為0-cell preflight失敗，沒有模型generation、沒有EvalPlus，也不構成generation retry或resume。本版會讀取該API欄位、以`strip().upper()`正規化後只接受`Q4_K_M`，並繼續要求digest逐字一致。

唯一人工生成指令（請由repository根目錄的PowerShell手動執行）：

```powershell
.venv\Scripts\python.exe scripts\run_mbpp_candidate_b_development60_replay.py generate --manifest artifacts\public_benchmark_governance\candidate_b_development60_replay_v1\manifest.json --manifest-sha256 cb6c36d5342da1096371946e58c5481291628ac28859a568ded95b11eada49e7
```

完成生成與evaluator-blind H0/H1 materialization後仍不得直接宣告功能結果；須由後續另行授權的EvalPlus與paired analysis依已凍結gate判定。
