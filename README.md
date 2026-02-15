# 🏆 旺宏科學獎——AI 自動化教育軟體生成研究

## 📌 專案名稱與定位

**中文**: 《系統級 Healer 與 MCRI 評測系統在 AI 自動化題目生成中的應用——以高中數學為例》

**英文**: *System-Level Healer and MCRI Evaluation Framework for AI-Automated Mathematics Problem Generation in Secondary Education*

**核心創新**: 首次提出並驗證「教育場景專用的 AI 代碼評分系統」(MCRI V4.2.2)，並證明「自動化修復機制 (Healer)」是落地的唯一解。

**最新突破 (2026-02-15)** 🚀:
- **Thinking Models (Qwen 3)**: 整合 14B 思維模型，具備長鏈推理能力 (CoT)。
- **Stub Injection Technology**: 創新的「Prompt 瘦身 + 執行期注入」技術，大幅降低 Token 消耗並消除幻覺。
- **Auto-Healing Pipeline**: 9 層修復機制穩定運行，成功解決 AI 生成的語法與邏輯錯誤。

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask-green)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/database-SQLite-lightblue)](https://www.sqlite.org/)
[![Qwen 2.5/3](https://img.shields.io/badge/AI-Qwen%2014B%20(Local)-purple)](https://huggingface.co/Qwen)
[![Science Fair](https://img.shields.io/badge/Status-Gold%20Medal%20Research-gold.svg)](docs/reports/GOLD_MEDAL_QUICK_REFERENCE.md)

---

## 🎯 研究目標與核心發現

**主要問題**: 
> *AI 生成的教育軟體代碼能否穩定用於真實教室？*

**研究假說**:
- H1: 簡單的 Prompt 工程無法保證代碼質量 (Ab1 - Bare)
- H2: 精心設計的 Prompt 提升品質但仍不夠 (Ab2 - Engineered)
- H3: 系統級修復機制 (Healer) 才能實現工業級穩定 (Ab3 - Healer)

**最新實驗數據 (FourArithmeticOperationsOfNumbers)** ⭐:
```
Ab1 (Bare):     Timeout / Logic Error (高失敗率)
Ab2 (Engineered): 成功生成，邏輯正確，偶發格式問題
Ab3 (Healer):   完美修復，具備 Stub Injection 與 Full Implementation，穩定運行 ✨
```

**科研貢獻**:
1. ✅ 首創「外在強健性測試」(Robustness Test) - 評估學生輸入容錯
2. ✅ 首創「教學適用性評分」(Pedagogy Score) - 評估數值友善度與視覺可讀性
3. ✅ 證明「自動化修復」(Healer) 的必要性，並發展出 **Stub Injection** 技術架構

---

## 📖 專案背景與現況 (Project Overview)

**現況**: 
本研究在旺宏科學獎 2026 年度中，已完成以下工作:
- ✅ 設計 MCRI V4.2.2 評測系統（4 層級 × 8 指標 = 100 分）
- ✅ 實現 Healer 9 層修復管道（從 whitespace 到 loop breaker）
- ✅ 整合 Qwen 3 (Thinking Model) 本地模型工作流
- ✅ **關鍵突破**: 解決了 Google AI API 依賴問題，轉向本地強大模型 (14B)

**下一步**: 擴展至更多高難度技能（如微積分、三角函數），驗證 Stub Injection 的普適性。

---

## 💡 核心想法與實驗邏輯 (Core Concept)

### 問題域分析

傳統的 AI 代碼評測系統 (HumanEval, MBPP) 只看「功能是否正確」，但教育場景需要評估：

| 維度 | 傳統系統 | 本研究 (MCRI) | 教育意義 |
|------|---------|--------------|---------|
| **功能正確性** | ✓ | ✓ (L1-L2) | 程式能否執行 |
| **學生輸入容錯** | ✗ | ✓ (L3.2) | 學生答錯的格式能否被系統理解 |
| **數值友善度** | ✗ | ✓ (L4.1) | 答案是否適合教學（如 3/4 而非 1039/4821） |
| **視覺可讀性** | ✗ | ✓ (L4.2) | 學生能否看懂輸出（LaTeX vs Python 語法） |

### 技術架構：Stub Injection (2026-02-15 New)

為了解決 LLM Context Window 限制與幻覺問題，我們採用了分離式注入策略：

1.  **Prompt 階段 (Stub Mode)**:
    只將工具的 **介面 (Interface)** 與 **Docstring** 注入 Prompt。
    *   *優點*: 節省 40-60% Token，讓 AI 專注於業務邏輯。
    *   *形式*: `class FractionOps: ...`

2.  **生成階段 (Full Injection)**:
    在 AI 生成代碼後，由 `code_generator.py` 自動注入 **完整實作 (Implementation)**。
    *   *優點*: 確保程式可執行，且邏輯統一由系統維護，不受 AI 隨機性影響。

---

## 🔬 實驗執行流程 (Experiment Workflow)

### Step 1: Golden Prompt Generation (Mode 4)
自動從資料庫讀取 MASTER_SPEC，經過 `PromptBuilder` 的 Stub 處理與 Safety Check，生成最佳化的 Prompt 檔案。

### Step 2: Code Generation (Mode 2)
讀取 Golden Prompt，透過 Qwen 3 模型生成代碼邏輯。

### Step 3: Healer Pipeline & Injection
系統自動修復語法錯誤 (Healer)，並注入完整工具庫 (Full Injection)。

### Step 4: MCRI Evaluation
執行生成的代碼，進行 L1~L4 全方位評測。

---

## 📊 檔案結構 (File Structure)

```
E:\Python\MathProject_AST_Research
├── core/                   # 核心邏輯
│   ├── code_generator.py   # [V10.2] 代碼生成與注入引擎
│   ├── ai_wrapper.py       # 模型呼叫介面
│   └── prompts/            # Prompt 工程模組
│       ├── prompt_builder.py        # Prompt 建構器
│       └── domain_function_library.py # 工具庫定義 (含 Stub 生成)
├── scripts/                # 工具腳本
│   ├── sync_skills_files.py # 主生成腳本
│   └── evaluate_mcri.py    # 評測腳本
├── experiments/            # 實驗數據
│   └── golden_prompts/     # 保存的 Golden Prompts (.txt)
├── skills/                 # 生成結果
│   └── (AI 生成的 .py 檔案)
├── docs/                   # 文件
│   ├── reports/            # 歸檔的部署報告與實驗記錄
│   └── 競賽文件/            # 科展相關文件
├── README.md               # 本文件
└── DOCUMENT_INDEX.md       # 文件索引
```

---

## 📄 授權與聯繫 (License & Contact)

本專案採用 **MIT License** 開源授權，歡迎教育工作者與開發者共同參與貢獻。

*   **專案負責人**: [Your Name/Team Name]
*   **聯繫信箱**: contact@smart-edu.ai

---
*Built with ❤️ for the future of education.*
