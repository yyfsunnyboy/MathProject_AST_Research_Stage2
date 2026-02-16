# 🧪 MathProject 實驗流水日誌 (Experiment Journal)

> 「所有的科學進展，都來自於對異常現象的執著追問。」

本文件記錄了專案開發過程中的關鍵決策、失敗嘗試、頓悟時刻與技術演進。

---

## 📅 2026-02-15: Stub Injection 技術突破 (里程碑 5)

### 💡 核心想法
我們在 Ab2 (Engineered Prompt) 遇到了一個嚴重的 **Token 效率與幻覺問題**。
- 將完整的工具代碼 (`IntegerOps`, `FractionOps`) 放進 Prompt 太佔空間 (Token 爆炸)。
- 但如果不給工具，AI 就會亂寫 (幻覺)。

**Action**: 我們發明了 **Stub Injection (樁代碼注入)** 技術。
1.  **Prompt 階段**: 只給 AI 看工具的「皮」 (Stubs: 介面定義 + Docstring)。
2.  **生成階段**: AI 呼叫這些工具。
3.  **執行階段**: `code_generator.py` 強制注入工具的「骨肉」 (Full Implementation)。
4.  **安全清理**: 使用 AST 解析器，強制移除 AI 可能「雞婆」自己實作的 Stub Class，確保系統工具是唯一真理。

### 📝 心路歷程
> 「我們不能信任 AI 寫的工具代碼，但我們必須信任它寫的業務邏輯。所以，讓 AI 負責『用工具』，我們負責『造工具』。」

### 📊 進步與退步
- **進步**: Token 消耗減少 60%，Prompt 更乾淨，邏輯解耦。
- **退步**: 系統複雜度增加，需要維護 Stub 生成器與清理器。

---

## 📅 2026-02-13: 擁抱 Thinking Models (里程碑 4)

### 💡 核心想法
Google AI API 的不穩定 (403 Errors) 迫使我們尋找替代方案。
同時，DeepSeek R1 與 Qwen 2.5/3 的崛起，證明了 **Test-Time Compute (Thinking)** 對於數學推理的重要性。

**Action**:
- 全面轉向 **Qwen 2.5-14B-Coder** 與 **Qwen 3** 本地模型。
- 不再依賴雲端 API，實現了實驗的可重現性與隱私安全。

### 📝 心路歷程
> 「如果不把思考過程 (Chain of Thought) 納入 Prompt，數學題的準確率永遠上不去。現在有了 Thinking Models，我們終於可以讓 AI 『先想再寫』。」

---

## 📅 2026-02-02: 發現 Prompt 層級衝突 (里程碑 3)

### 💡 核心想法
在 3x3 實驗設計中，我們驚訝地發現 **Ab2 (Engineered Prompt) 的表現有時甚至不如 Ab1 (Bare Prompt)**。
經過深入排查，我們發現了 `MASTER_SPEC` (高層指令) 與 `Details` (底層指令) 之間的衝突。

**Action**:
- 撰寫了 [Prompt 層級衝突案例研究](03_實驗過程/🧬3x3實驗設計詳解與過程.md)。
- 確立了「變因分離」原則：Ab1 測智商，Ab2 測 Prompt，Ab3 測 Healer。

### 📝 心路歷程
> 「我們以為給 AI 越多指令越好，結果指令之間打架了。AI 陷入了『父子騎驢』的困境。我們必須簡化指令層級。」

---

## 📅 2026-01-29: Healer 的誕生 (里程碑 2)

### 💡 核心想法
AI 生成的代碼總是有 5-10% 的語法錯誤或無限迴圈。
傳統做法是 Retry (重試)，但這很浪費時間且不一定有效。
我們決定實作 **Self-Healing (自我修復)** 機制。

**Action**:
- 開發 **9 層 Healer Pipeline**。
- 從簡單的 Regex (正則) 修復，進化到強大的 AST (語法樹) 修復。
- 引入 `Safe Eval` 與 `Loop Breaker` 防止惡意代碼與死循環。

### 📝 心路歷程
> 「Regex 只能修皮毛，AST 才能修筋骨。當我們看到 Healer 自動修好了那些缺括號、縮進錯誤的代碼時，真的覺得這個系統『活』過來了。」

---

## 📅 2026-01-15: MCRI 評測系統確立 (里程碑 1)

### 💡 核心想法
如何證明我們的系統比別人好？
只看「程式能跑」是不夠的 (L1)。
我們需要一個更全面的指標，關注教育價值。

**Action**:
- 提出 **MCRI V4.2 架構**。
- **L3 (Robustness)**: 測試學生亂輸入時系統會不會崩潰。
- **L4.1 (Numeracy)**: 測試數字漂不漂亮 (教學友善度)。

### 📝 心路歷程
> 「教育軟體的重點不是代碼寫得多漂亮，而是學生用起來順不順手。如果答案是 3.1415926535... 而不是 \pi，那這個題目就是失敗的。」

---


---

## � 歷史回溯 (Archive Chronicles)

以下紀錄了專案早期的關鍵技術突破與除錯歷程，這些經驗奠定了今日架構的基石。

### 📅 2026-02-08: Healer V2.8 與重複定義之戰
*   **事件**: 發布 Healer V2.8 (Critical Fix)。
*   **背景**: 在 Ab3 測試中，發現 AI 生成的代碼中這包含兩個 `class IntegerOps` 定義（一個System完整版，一個AI殘廢版），導致 `Redefinition Error` 或 `AttributeError`。
*   **解決**: 實作了 `remove_duplicate_class_definitions` (Regex層級)，這是後來 V47.16 AST Cleanup 的前身。
*   **意義**: 這是我們第一次意識到「Tool Injection」與「AI Generation」之間的衝突，開啟了與 AI 幻覺對抗的長期戰爭。
*   **詳情**: [REGEX_HEALER_V2_8_DEPLOYMENT_REPORT.md](99_歷史歸檔/REGEX_HEALER_V2_8_DEPLOYMENT_REPORT.md)

### 📅 2026-02-04: MCRI V4.4 - 追求數學之美
*   **事件**: MCRI 評測系統升級至 V4.4。
*   **核心**:
    *   **L4.3 (Quality Control)**: 新增扣分邏輯（零係數項 -10分，符號未簡化 -3分）。
    *   **L5 (Complexity)**: 引入 SymPy 進行數學複雜度分析。
*   **意義**: 標誌著我們從「讓程式能跑 (L1/L2)」轉向「讓題目好用 (L4)」。我們開始關注 `0x + 3` 這種「合法但愚蠢」的數學表達式。
*   **詳情**: [MCRI_V4_4_DEPLOYMENT_SUMMARY.md](99_歷史歸檔/MCRI_V4_4_DEPLOYMENT_SUMMARY.md)

### 📅 2026-02-01: The "Identity" Crisis (Ablation Bug)
*   **事件**: 發現嚴重實驗 Bug - Ab1/Ab2/Ab3 產出的檔案內容竟完全相同。
*   **原因**: `sync_skills_files.py` 中的路徑邏輯錯誤，導致它總是讀取並覆蓋同一個檔案，或者根本沒有正確傳遞 `ablation_id` 參數。
*   **反思**: 這是專案最危險的時刻。如果未被發現，所有關於「Ab3 優於 Ab1」的結論都將是偽造的。這教會了我們：**Verify, Verify, Verify (驗證再驗證)**。
*   **詳情**: [Ablation_Bug_修復報告_20260201.md](99_歷史歸檔/Ablation_Bug_修復報告_20260201.md)

### 📅 2026-02-01: Loop Breaker V2.0 - AST 的勝利
*   **事件**: Loop Breaker 從 Regex 升級為 AST。
*   **背景**: 早期的 Regex 暴力替換 (`while True` -> `for _ in range`) 經常破壞縮排，導致 `IndentationError`。
*   **解決**: 引入 `ast` 模組來解析迴圈結構，並自動調整 `break`/`continue` 的縮排。
*   **意義**: 這是我們第一次在修復機制中引入 AST，證明了單靠 Regex 是無法處理 Python 複雜語法的。這直接啟發了後來 V47.16 的 Domain Stub Cleanup。
*   **詳情**: [Loop_Breaker_V2.0_完成總結.md](99_歷史歸檔/Loop_Breaker_V2.0_完成總結.md)

---

