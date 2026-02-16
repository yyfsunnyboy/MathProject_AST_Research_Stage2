---
name: math-problem-generator
version: v1
description: 生成可執行的 Python 程式碼作為數學題目,確保題目品質與程式碼穩定性 (Base on Scaffolding)
---

# Math Problem Generator Skill

## 核心任務
將使用者的題目需求轉換為一段 Python 程式碼，該程式碼執行後會：
1. **題目生成 (Question Generation)**: 生成符合 LaTeX 格式的數學題 (question_text)
2. **答案計算 (Answer Calculation)**: 計算出正確答案 (correct_answer)
3. **格式化輸出 (Standardized Output)**: 確保輸出符合 JSON 規範

## 生成規範 (Scaffolding Standards)
### 1. 程式碼結構
- 必須實作 `def generate(level=1, **kwargs)` 函數
- **禁止**自行定義基礎類別 (如 `RadicalOps`, `IntegerOps`)，必須使用注入好的 Domain API
- 使用 `random.seed()` (若需要重現性) 或 `random.randint` 確保題目多樣性

### 2. 資料流與變數
- **Question**: 使用 LaTeX 格式 (數學式用 `$...$` 包裹)
- **Answer**: 必須是字串格式 (`str`)，且必須是最簡形式
- **Mode**: 固定為 `1` (Text Mode)

### 3. 無副作用 (Side-effect Free)
- 禁止使用 `input()` 阻塞執行
- 禁止使用 `print()` 作為輸出方式 (僅用於調試)
- 禁止無限迴圈 (`while True`)

## 品質檢查 (Healer Integration)
在提交程式碼前，系統會自動執行以下檢查：
- [x] **Regex Healer**: 清理 Markdown 標記、修復常見語法錯誤 (`++` -> `+`)
- [x] **AST Healer**: 檢查危險函數 (`eval` -> `safe_eval`)、修復未定義變數
- [x] **Dynamic Sampler**: 實際執行生成函數 3 次，確保無 Runtime Error

## 版本控制
- **v0 (Bare)**: 僅使用自然語言 Prompt (Ab1)
- **v1 (Scaffolding)**: 引入 Domain Function Library 與標準化 Prompt (Ab2) - **[Current]**
- **v2 (Self-Healing)**: 引入 Advanced Healer Pipeline (Ab3)

## 相關檔案
- `evals/evals.json`: 標準測試集 (Benchmark)
- `scripts/validate_code.py`: 程式碼驗證腳本
