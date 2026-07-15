# 🧬 Math-Master: Stage2 Agent Operational Guidelines (GEMINI.md)

本文件定義了在本專案（`MathProject_AST_Research_Stage2`）中進行開發、實驗與評估的 Agent 執行規範。所有 AI 助理（包括 Antigravity 與其他同類 Agent）在讀取此 Constitution 後，必須嚴格遵守以下條款。

---

## 🛡️ 1. 工作目錄與權限規範

*   **唯一允許寫入之 Repo**：本專案資料夾 `MathProject_AST_Research_Stage2` 是唯一允許寫入、修改與測試的開發分支。
*   **唯讀位置限制**：任何位於 `AST_experiment` 或外部正式 `results` 目錄下的歷史數據與檔案均為**唯讀（Read-Only）**，禁止任何寫入、移動或修改。
*   **互斥寫入原則**：同一時間僅允許單一 Agent 對 Stage2 Repo 進行寫入與程式碼變更，防止多 Agent 協同寫入衝突。

---

## 🔍 2. 啟動檢查與日誌

*   **每一輪啟動之首要任務**：在進行任何代碼變更或執行 runner 前，Agent 必須先依序執行並檢查：
    1.  `Get-Location` (確認所在目錄)
    2.  `git branch --show-current` (確認為 target branch，預設為 `main`)
    3.  `git rev-parse HEAD` (比對當前 HEAD)
    4.  `git status --short` (確保 working tree 乾淨)
*   如果工作樹不乾淨或 branch/HEAD 不符合實驗預期，必須**立即停止**並向使用者回報。

---

## 📊 3. 實驗與評量守則 (ITT & 三帳分列)

*   **ITT 原則**：所有測試之第一次生成射（first attempt）結果固定為 ITT 基準，**嚴禁**使用 retry（多次生成）結果覆蓋第一次的 Observed 失敗輸出。
*   **三帳分列**：任何實驗報告與評測結果必須將 **Observed（Raw）**、**Pipeline-corrected（Scaffold 修正）** 與 **Post-Healer（Healer 修復）** 分立三帳進行獨立統計，如實反映 Healer 的真實改進率。
*   **探索與確證分離**：不得將在探索性校準資料（exploration set）上優化出來的 Healer 規則 Replay 結果，宣稱為「凍結後驗證的 confirmatory evidence」。

---

## 🚫 4. 嚴格禁止修改與執行事項

未獲得使用者的明確授權前，Agent 禁止執行以下操作：

*   **禁止跑模型與正式實驗**：禁止呼叫 LLM API 進行大規模生成、Healer replay、或執行官方的 EvalPlus 測試。
*   **禁止修改敏感檔案**：禁止修改任何正式 Excel 數據、凍結的 prompt 模板、獨立 Oracle 求解合約、或正式的實驗 results 檔案。
*   **禁止移動或刪除 evidence**：禁止修改或刪除 `artifacts/fail_to_fail_forensics/` 底下的任何證據，除非先建立對應的 manifest 並取得明確授權。
*   **禁止無依賴判定**：不可單憑檔名包含 `temp`、`old`、`processed` 或是 `archive` 就直接判定檔案無引用而將其刪除，必須經由專案全局引用查證。

---

## 🧪 5. 研究宣稱與語義邊界

Agent 在撰寫研究報告或給予 User 回饋時，必須保持極高的學術誠實度，**禁止**出現以下誇大或不實的主張：

*   **禁止宣稱「零語意風險」**：Healer 機制有其語意介入窗口限制，不可宣稱修復具備「100% 確定性」或「零語意風險」。
*   **禁止宣稱「合法縮小分母」**：在 K12 數學出題中，根式的化簡或分母處理必須嚴格遵守數學 Truth，不得採用非數學規範的 ad-hoc 方法。
*   **禁止宣稱「Ab2g 是最佳條件」**：Ab2g 僅是實驗中的一種消融條件，不應將其定性為唯一的最佳實踐。
*   **禁止宣稱 seed 逐位重現**：不得宣稱 seed 能使模型（特別是雲端 thinking models）的 CoT 推理或輸出達到 100% 位元級（bit-level）重現。

---

## 💾 6. Git 提交與收尾規範

*   **關鍵里程碑提交**：僅在順利通過所有核心離線測試（不涉及模型）後，才在關鍵里程碑進行 commit & push。
*   **規範性 Commit Message**：使用 Conventional Commits 格式（例如 `docs: refresh current research entrypoints`）。
*   **路徑真實性**：在撰寫任何文檔連結前，Agent 必須先查證 Repo 的真實檔案狀態，禁止引用不存在、或已被 git 刪除的 dangling 連結。