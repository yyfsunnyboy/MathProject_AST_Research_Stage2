# MBPP+ Healer v0 validation P0 prospective qualification操作指南

本規格固定從既有frozen split機械載入20題validation，只使用P0官方prompt、qwen3.5:9b既有正式model digest與seeds 11/22/33/44/55。共100個raw generation cells與200個H0/H1 evaluation accounts。沒有Scaffold，H1不重新生成。

本準備輪已完成zero-model preflight，沒有呼叫Ollama或EvalPlus。人工執行前必須確認固定run output path不存在；runner拒絕resume、retry、selective rerun與overwrite。任何一格失敗時只保留已durably persisted的journals，禁止自行補跑。

## 唯一人工執行指令

在repository根目錄的Windows PowerShell執行：

```powershell
C:\Users\yehya\Documents\GitHub\MathProject_AST_Research_Stage2\.venv\Scripts\python.exe scripts\run_mbpp_healer_v0_validation_p0.py generate --manifest artifacts\public_benchmark_governance\healer_v0_validation_p0_v1\manifest.json --manifest-sha256 f32d67f62f1af9de5f07db489700f940edd7bf1e348f90275a4d9177a6b53fb0
```

此指令只完成100次generation與evaluator-blind H0/H1 materialization；不執行EvalPlus。後續評估必須另由新Milestone授權。
