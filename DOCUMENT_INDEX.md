# 📑 MathProject_AST_Research_Stage2 專案文檔與檔案總索引

本索引依據 Repository 中實際存在、且由 Git 追蹤之最新檔案結構進行編排。

---

## 🗂️ 1. CURRENT CORE (目前核心代碼)

決賽 Rebuild 評估、Healer 運作及出題 pipeline 的最小必要代碼集合。

*   **決賽重建適配器與評估器**：[agent_tools/finals_rebuild/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/)
    *   主重建消融 Pipeline：[pipeline.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/pipeline.py)
    *   數學出題測試生成 Runner：[math_generation_runner.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/math_generation_runner.py)
    *   外部通用基準 Runner：[public_benchmark_runner.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/public_benchmark_runner.py)
    *   Core  punctuation 修正器：[core_adapter.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/core_adapter.py)
    *   Spec 數學合約修正器：[spec_adapter.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/spec_adapter.py)
*   **出題演算法與 Scaffold**：
    *   JIT 出題 Scaler：[core/engine/scaler.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/engine/scaler.py)
    *   出題分類器：[core/engine/classifier.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/engine/classifier.py)
    *   Scaffold 數學基底庫：[core/scaffold/domain_libs.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/scaffold/domain_libs.py)
    *   出題技能規則與 alias 對照：[core/skill_policies/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/skill_policies/)
*   **技能特化 Prompt 定義**：[agent_skills/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_skills/)
    *   包含四個核心技能資料夾的 `skill.json`、`SKILL.md`、`prompt_benchmark.md` 與 `prompt_liveshow.md`。

---

## 🔬 2. ACTIVE RESEARCH DESIGN (目前研究設計)

本研究的正式實驗與適配器合約設計白皮書。

*   **數學出題軌任務設計**：
    *   CE115 數學任務規格設計：[docs/研究設計/CE115_Math_Pilot_Task_Design.md](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/研究設計/CE115_Math_Pilot_Task_Design.md)
    *   Ab2d 技能合約與能力審計：[docs/experiments/ab2d_skill_contract_and_capability.md](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/experiments/ab2d_skill_contract_and_capability.md)
    *   Ab2d 本地 Prompt 設計 (2026-07-14)：[docs/experiments/ab2d_local_prompt_design_20260714.md](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/experiments/ab2d_local_prompt_design_20260714.md)
    *   Ab2g 核心數學評量設計 (2026-07-14)：[docs/experiments/ab2g_math_core_qualification_design_20260714.md](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/experiments/ab2g_math_core_qualification_design_20260714.md)
*   **外部效度對照軌設計**：
    *   HumanEval+ / MBPP+ 跨域實驗啟動規格：[docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/HumanEval+／MBPP+ 跨域 Scaffold × Healer 實驗啟動規格.md)

---

## 📊 3. CURRENT EVIDENCE (正式研究證據)

凍結後外部驗證的正式證據檔案，不可隨意移動或刪除。

*   **Healer-vNext 法醫學分析（對照組對決證據）**：[artifacts/fail_to_fail_forensics/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/artifacts/fail_to_fail_forensics/)
    *   Qwen-8B 與 Gemini 在 HumanEval+/MBPP+ 上的 raw/healed 對比 manifest、分類 CSV 與 raw/healed 代碼的 AST/normalized diff。
*   **實時評估證據與結果記錄 (2026-07)**：[docs/experiments/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/experiments/)
    *   包含以 `20260714` 命名之 smoke/replay 驗證報告 md 檔，及 [docs/experiments/results/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/experiments/results/) 下的 `.jsonl` 輸出結果。
*   **歷史對比之 Replay 輸入源**：
    *   在 `experiments/results/` 下有 7 個特定 Ab2 歷史生成結果檔（被 `test_legacy_migration.py` 所依賴的 byte-identity 驗證源）。

---

## 🧪 4. TESTS AND VALIDATION (測試與驗證)

*   **重建測試套件**：[tests/finals_rebuild/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/tests/finals_rebuild/)
    *   包含 pipeline、adapters、evaluators 等 39 個離線測試。
*   **法醫學過濾驗證測試**：[tests/test_fail_to_fail_forensics.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/tests/test_fail_to_fail_forensics.py)
*   **法醫學數據產生器**：[exp1_benchmark/fail_to_fail_forensics.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/exp1_benchmark/fail_to_fail_forensics.py)
*   **一鍵驗證環境與測試指令碼**：[scripts/verify_finals_rebuild.sh](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/scripts/verify_finals_rebuild.sh)

---

## 📚 5. LEGACY REFERENCE (歷史歸檔與舊系統)

此處檔案僅表示**「目前非主研究入口，已脫離主開發線」**，但不等於可以直接刪除。

*   **舊 Flask Web UI 系統**：[app.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/app.py), [models.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/models.py), [templates/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/templates/), 路由模組 [core/routes/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/routes/)。
*   **過時大會報告與科展筆記**：
    *   歷史競賽文檔：[docs/競賽文件/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/競賽文件/)
    *   決賽空歸檔目錄：[docs/決賽文件/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/決賽文件/)
    *   *註：早期大會報告 `Generator_Census_Validity_Executive_Verdict.md` 已在 commit `fd42f9f5` 被歸檔移出工作區，可由 Git 歷史檢索。*
*   **舊歷史 Healers 實作**（新 pipeline 預設 disabled）：
    *   [core/healers/ast_healer.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/healers/ast_healer.py)
    *   [core/healers/regex_healer.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/healers/regex_healer.py)
*   **過時實驗與資料庫維護腳本**：
    *   未引用的舊腳本：[scripts/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/scripts/) 直接目錄下的大部分 Python 檔（例如 `sync_skills_files.py`、`run_experiment.py`）。
    *   臨時研發腳本：[scripts/temp/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/scripts/temp/) 下的 50+ 個 python 腳本。

---

## ⚠️ 6. UNCERTAIN / DO NOT DELETE (有依賴之舊檔案)

*   **具有隱性依賴之 legacy 腳本**：[scripts/evaluate_mcri.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/scripts/evaluate_mcri.py)
    *   *說明*：雖然屬於舊評測腳本，但其內部的 `evaluate_math_hygiene` 與 `analyze_code_robustness` 仍被核心出題引擎 [core/engine/scaler.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/core/engine/scaler.py) 直接 import。**禁止刪除**，需待後續重構解耦。
*   **未建立 provenance / manifest 之備份代碼**：[skills/backup/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/skills/) (包含 `skills/` 底下數個 `backup_` 目錄)
    *   *說明*：這 900+ 個由舊模型生成的備份 `.py` 檔案目前無外部調用，但為防範數據遺失，必須在建立明確來源記錄後，於第二輪清理時再決定保留、封存或刪除。
