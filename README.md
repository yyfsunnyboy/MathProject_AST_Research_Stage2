# 🏆 MathProject_AST_Research_Stage2: Small but Precise

本專案為旺宏科學獎決賽研究「小型在地化模型透過工程干預（Scaffold + Healer）在特定任務上超越雲端大模型」的第二階段研究 Repository。我們聚焦於系統級修復機制（Healer）在數學出題程式生成任務中的語意安全與可靠度驗證。

---

## 📌 1. 專案目前定位與核心問題

*   **研究主軸**：本專案仍以**「數學出題程式生成」**為主要研究對象。
*   **核心問題**：領域特化、確定性的 **AST Active Healer**，能否在明確且安全的介入窗口（Intervention Window）中，有效提高邊緣模型（例如 Qwen-8B/14B）生成數學出題程式의 可靠度。
*   **方法論主軸**：聚焦於**「失敗驅動（Failure-driven）、語意安全（Semantic Safety）、凍結後外部驗證（Post-frozen External Verification）」**的 Scaffold ＋ deterministic Healer 建構方法。本專案不以模型自主的 ad-hoc 生成或不受控的 retry 為手段，而是依靠嚴謹的後端單一真相（Source of Truth）進行 deterministic 出題與求解。

---

## 🔬 2. 兩條平行研究軌

本研究透過以下兩條正式軌道進行雙重驗證：

1.  **數學出題程式軌 (Math Track)**：
    *   對象為 **CE115 數學出題任務**（含 G1–G6 評量、多項式四則、根式四則與 RPM 轉速換算等問題）。
    *   以領域特化的 **Domain Scaffold** 為基礎，結合特製的 **Healer 邊界限制**，並導入獨立的 **Oracle 解題合約**。
2.  **公開基準軌 (Public Benchmark Track)**：
    *   對象為 **HumanEval+／MBPP+** 數據集（透過官方 EvalPlus 引擎評估）。
    *   本軌道僅用作**外部效度（External Validity）**與 **Regression Safety** 驗證，用以觀察通用代碼修復的安全介入窗口，**不取代**數學主研究的主軸地位。

---

## 📊 3. 評量與驗證原則

為確保研究證據的學術嚴謹度，本專案執行以下評量原則：

*   **ITT 原則 (Intent-to-Treat)**：第一射（first attempt）結果固定為 ITT 基準，不允許透過多次重試（retry）或篩選最佳輸出覆蓋第一次的 Observed 結果。
*   **三帳分列**：所有生成結果依 **Observed（未修復）**、**Pipeline-corrected（Scaffold 修正）**、與 **Post-Healer（Healer 修復後）** 三帳平行分列，透明呈現每一階段的改進。
*   **外部驗證（No Self-Grading）**：答案正確性、執行狀況、合約相符性與輸出格式均由外部 evaluator / oracle 進行獨立驗證，**不再以自建的 MCRI 100 分加權總分作為主要研究證據**。
*   **Eligibility 與修復的區別**：Eligibility（適用性/符合介入資格）僅代表候選介入窗口，不等於 Healer 修復成功，兩者數據必須分離統計。

---

## ⚠️ 4. 證據限制與邊界

*   **Healer 版本區分**：必須嚴格區分 **Minimal Core／原先凍結的正式 Healer** 與探索性開發的 **Safe Historical Healer**。
*   **避免循環論證**：同批校準/探索資料上所開發出的 Healer 規則與 replay 結果，**不得**包裝成凍結後驗證的 confirmatory evidence（確證性證據）。
*   **Pilot 狀態標示**：目前規劃的 corrected four-task pilot 若僅有 design 與 manifest 結構、尚未完成大規模生成者，在文件中必須如實標示為「設計/探索階段」，不得宣稱已取得 confirmatory results。

---

## 🚀 5. 快速入口與結構導引

本專案目前的決賽 rebuild 評估完全脫離了 Flask Web UI 機制，全面使用離線的專屬 runner 與測試集。以下為核心入口：

*   **核心 Runner**：
    *   決賽重建 Pipeline：[pipeline.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/pipeline.py)
    *   數學生成執行器：[math_generation_runner.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/math_generation_runner.py)
    *   外部基準執行器：[public_benchmark_runner.py](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/agent_tools/finals_rebuild/public_benchmark_runner.py)
*   **研究設計與證據**：
    *   CE115 任務設計：[CE115_Math_Pilot_Task_Design.md](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/研究設計/CE115_Math_Pilot_Task_Design.md)
    *   Ab2d 技能合約與審計：[ab2d_skill_contract_and_capability.md](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/docs/experiments/ab2d_skill_contract_and_capability.md)
    *   Healer-vNext 法醫學驗證證據：[fail_to_fail_forensics/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/artifacts/fail_to_fail_forensics/)
*   **一鍵驗證腳本**：
    *   決賽 Rebuild 檢查：[verify_finals_rebuild.sh](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/scripts/verify_finals_rebuild.sh)
*   **測試套件**：
    *   決賽 Rebuild 測試集：[tests/finals_rebuild/](file:///c:/Users/yehya/Documents/GitHub/MathProject_AST_Research_Stage2/tests/finals_rebuild/)
