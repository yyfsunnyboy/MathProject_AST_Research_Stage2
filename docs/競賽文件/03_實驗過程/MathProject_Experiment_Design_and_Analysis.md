# MathProject 實驗設計與分析報告 (Experiment Design and Analysis)

> **版本**: V1.0 (2026-02-15)
> **目的**: 闡述實驗方法論 (Methodology)、評測標準 (MCRI) 與關鍵實驗發現。

---

## 🔬 1. 實驗方法論：3x3 Full Factorial Design

為了科學地驗證「Prompt Engineering」與「Self-Healing」的獨立貢獻，我們設計了嚴謹的 **3x3 實驗矩陣**。

### 變因定義 (Variables)

1.  **控制變因 (Independent Variables)**:
    *   **Level of Prompt Engineering**:
        *   **Ab1 (Bare Prompt)**: 僅給出最基礎的指令 ("寫一個數學題生成器")，無工具庫。
        *   **Ab2 (Engineered Prompt)**: 提供完整的 MASTER_SPEC、工具 Stub、格式規範。
        *   **Ab3 (Healer Integration)**: 同 Ab2，但開啟後端修復機制。

    *   **Sample Diversity**:
        *   **S1 (Simple)**: 整數運算 (基礎)
        *   **S2 (Complex)**: 分數/根號/多項式 (進階)
        *   **S3 (Abstract)**: 函數/微積分 (抽象)

2.  **依變項 (Dependent Variables)**:
    *   **MCRI Score** (0-100 分)
    *   **Success Rate** (L1 Pass Rate)
    *   **Token Efficiency**

### 實驗假設 (Hypotheses)
*   **H1**: Ab2 > Ab1 (Prompt Engineering 能顯著提升 L2/L4 分數)。
*   **H2**: Ab3 > Ab2 (Healer 能顯著提升 L1 通過率與 L3 強健性)。
*   **H3**: 在複雜題目 (S2/S3) 中，Ab1 將完全失效 (Score ≈ 0)。

---

## 📊 2. MCRI 評測系統 (V4.2.2)

傳統的 `Pass@k` 指標只能衡量「程式會不會崩潰」，無法衡量「題目好不好」。
我們提出了 **MCRI Framework** (Modular Code Reliability Index)。

### 評分權重 (Total: 100)

#### **L1: Execution Integrity (20%)**
*   程式能否在沙箱中編譯並執行？
*   是否在 5 秒內回傳結果？(Timeout Check)

#### **L2: Technical Compliance (20%)**
*   回傳格式是否符合 Schema？(`{'question_text': ..., 'correct_answer': ...}`)
*   變數命名是否規範？

#### **L3: Robustness & Fairness (30%)**
*   **L3.1 Internal Consistency**: `check(correct_answer)` 必須回傳 True。
*   **L3.2 External Robustness**: 模擬學生輸入各種變體 (如 `2/3`, `0.666`, `2 / 3`)，程式能否正確判定？**(這是最難的一關)**。

#### **L4: Pedagogical Quality (30%)**
*   **L4.1 Numeracy**: 數字是否「漂亮」？(避免分母 > 1000, 無限小數位)。
*   **L4.2 Visuals**: 是否正確使用 LaTeX 格式？(`\frac{1}{2}` vs `1/2`).

---

## 📈 3. 關鍵實驗發現 (Key Findings)

### 發現 A: Prompt 層級衝突 (The Hierarchy Conflict)
在 Ab2 實驗中，我們發現一個反直覺現象：**過度詳細的 Prompt 指令反而導致模型困惑**。

*   **現象**: 當我們要求「只能使用 `IntegerOps`」同時又要求「生成分數題目」時，模型崩潰了。
*   **根因**: MASTER_SPEC (High Level) 與 Tool Constraints (Low Level) 發生邏輯衝突。
*   **解法**: 引入 **Stub Injection**，讓模型只需關注「接口調用」，隱藏實作細節，消除了上下文中的衝突資訊。

### 發現 B: Healer 的必要性
*   **數據**:
    *   Ab1 Pass Rate: **15%** (大量語法錯誤)
    *   Ab2 Pass Rate: **65%** (邏輯正確但偶爾格式錯)
    *   Ab3 Pass Rate: **98%** (Healer 修復了絕大多數格式問題)
*   **結論**: 即使是最好的 Prompt (Ab2)，也無法保證 100% 的語法正確性。**Healer 是邁向工業級穩定的最後一哩路**。

### 發現 C: 本地推理模型 (Thinking Models) 的崛起
*   從 Google Gemini 轉向 Qwen 3 後，我們觀察到 **L4 (Pedagogy)** 分數顯著提升。
*   Thinking Process (CoT) 讓模型能先「規劃」出題邏輯，再「撰寫」代碼，大幅減少了邏輯漏洞。

---

## 📝 4. 案例研究：FourArithmeticOperations

以 `jh_數學1上_FourArithmeticOperationsOfNumbers` 為例：

| 指標 | Ab1 (Bare) | Ab2 (Engineered) | Ab3 (Healed) |
| :--- | :--- | :--- | :--- |
| **L1 (執行)** | Fail (Timeout) | Pass | Pass |
| **L2 (格式)** | Fail (Missing Keys) | Pass | Pass |
| **L3 (強健)** | N/A | 60分 (字串比對) | **95分** (AST解析) |
| **L4 (教學)** | N/A | 80分 | **100分** |
| **總分** | **0** | **78** | **98** |

這證明了我們的架構 (Ab3 + Stub Injection) 是目前最佳解決方案。

---
*文件整理: MathProject Team*
