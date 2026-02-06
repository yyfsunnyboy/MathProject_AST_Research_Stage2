# Ablation Prompt 問題根源分析

## 🔍 問題總結

剛才生成的三個 Ablation 檔案出現以下問題：

### Ab1 (Bare Prompt) 的問題
1. **數學計算錯誤**: `f"12{a}x + 6{b}"` → 應該是 `f"{12*a}x + {6*b}"`
2. **字串跳脫錯誤**: `'f\'\'\'(x)'` → 應該是 `"f'''(x)"`
3. **檔案末尾有無效文字**: Python 程式碼後直接接中文說明（未註解）

### Ab2 (Engineered Prompt) 的問題
1. **clean_latex_output 誤用**: 生成的程式碼錯誤地呼叫 `clean_latex_output(q)`，導致 LaTeX 被轉成佔位符

### Ab3 (Full Healer) 的狀態
- ✅ **完全正確** - Advanced Healer 自動修復了 4 個問題

---

## 📊 實驗設計回顧

### 三個 Ablation 的設計目的

```python
# Ablation 1: Bare Prompt (測試模型原生能力)
- Prompt: BARE_PROMPT_TEMPLATE (簡化的自然語言提示)
- Tools: 無 (僅 random, math 等標準庫)
- Healer: 無
- 目的: 測試 AI 在最少指導下的表現

# Ablation 2: Engineered Prompt (測試提示工程效果)
- Prompt: UNIVERSAL_GEN_CODE_PROMPT + MASTER_SPEC + Domain Functions
- Tools: PERFECT_UTILS + Domain Helpers
- Healer: 無
- 目的: 測試精密設計的提示詞 + 工具注入能提升多少

# Ablation 3: Full Healer (測試自癒機制)
- Prompt: 同 Ab2
- Tools: 同 Ab2
- Healer: Regex + AST 雙重修復
- 目的: 測試自癒機制能救回多少問題
```

---

## 🎯 問題根源分析

### 1. Ab1 的問題是「BARE_PROMPT 設計不良」嗎？

**答案：部分是，但這也是實驗設計的一部分**

#### 當前 BARE_PROMPT_TEMPLATE 的問題：

```python
BARE_PROMPT_TEMPLATE = """【角色設定】
你是一位國中數學老師的「出題助理」。

【任務說明】
請幫我寫一個 Python 程式，用來自動生成數學題目。
★ 題目主題是：「{topic}」（請務必針對此主題出題，不要生成其他類型的題目）
這個程式需要隨機產生數字，每次執行都能變換數值。
請使用跟課本一樣的格式表達數學式子。

【參考例題】
以下是我們想模仿的題目類型（請參考這個邏輯來寫程式）：
{textbook_example}

【程式要求】
1. 請寫成兩個函式：
   - `def generate(level=1, **kwargs)`: 生成題目
   - `def check(user_answer, correct_answer)`: 檢查答案是否正確

2. `generate` 函式要回傳一個字典 (Dictionary)，包含以下欄位（請照抄 key 名稱）：
   - 'question_text'
   - 'answer'
   - 'correct_answer'
   - 'mode': 1

3. `check` 函式請回傳一個字典，包含：
   - 'correct': True 或 False
   - 'result': 回傳 '正確' 或 '錯誤'

4. 請使用 Python 的 standard library (如 random, math) 即可。

請直接給我 Python 程式碼，不要解釋。
"""
```

#### BARE_PROMPT 的設計缺陷：

1. **缺少字串格式化範例**
   - ❌ 沒有說明如何正確使用 f-string
   - ❌ 沒有警告字串跳脫問題
   - → 導致: `f"12{a}x"` (錯誤拼接) 和 `'f\'\'\'(x)'` (跳脫錯誤)

2. **缺少程式碼純淨度要求**
   - ❌ 沒有說明「請直接給我 Python 程式碼」的精確定義
   - → 導致: 檔案末尾出現未註解的中文說明

3. **缺少數學計算指導**
   - ❌ 沒有範例說明如何計算導數
   - ❌ 沒有提醒「乘法運算符號不能省略」
   - → 導致: `12{a}` 而非 `{12*a}`

#### 但這是否應該修正？

**實驗設計的兩難：**

- **選項 A: 改進 BARE_PROMPT** → 提升 Ab1 品質
  - ✅ 優點: 獲得更可用的 Baseline
  - ❌ 缺點: **失去「模擬真實用戶」的對照組意義**
  - ❌ 缺點: Ab1 vs Ab2 的差距變小，無法量化提示工程的價值

- **選項 B: 保持 BARE_PROMPT 簡陋** → 維持實驗對照組
  - ✅ 優點: **真實反映「一般用戶」的提示品質**
  - ✅ 優點: 凸顯 Ab2 (工程化) 和 Ab3 (Healer) 的價值
  - ❌ 缺點: Ab1 品質較差，可能無法通過基本測試

---

### 2. Ab2 的問題需要從「源頭修改」嗎？

**答案：是的，這是一個真正的 Bug，需要修正**

#### Ab2 的問題：

```python
# 錯誤的生成結果 (Ab2)
derivative_symbols_latex = " 與 ".join(_deriv_symbol_latex(order) for order in derivative_orders_list)
q = f"已知 $f(x) = {poly_latex}$，求 ${derivative_symbols_latex}$。"
q = clean_latex_output(q)  # ❌ 錯誤！會把 LaTeX 轉成佔位符

# 正確的應該是 (Ab3)
derivative_symbols_latex = ' 與 '.join((_deriv_symbol_latex(order) for order in derivative_orders_list))
q = f'已知 $f(x) = {poly_latex}$，求 ${derivative_symbols_latex}$。'
# ✅ 不呼叫 clean_latex_output，因為已經是 LaTeX 格式
```

#### 為什麼 Ab2 會產生這個 Bug？

1. **UNIVERSAL_GEN_CODE_PROMPT 中有關於 clean_latex_output 的說明**
   - AI 學到了「應該呼叫 clean_latex_output」
   - 但 AI 不理解「Domain 函數已經處理好 LaTeX」的隱性規則

2. **缺少明確的 Domain 函數使用規範**
   - Prompt 說：「使用這些 Domain 函數」
   - 但沒說：「Domain 函數的輸出已經是 LaTeX，不要再 clean」

#### 解決方案：

**必須修改 `core/prompts/prompt_builder.py` 的 UNIVERSAL_GEN_CODE_PROMPT**

在 Domain 函數說明區塊加入：

```python
⚠️ Domain 函數特殊規則：
- _poly_to_latex(), _deriv_symbol_latex() 等 Domain 函數的輸出「已經包含 $ 符號」
- 使用這些函數時，「不要」再呼叫 clean_latex_output()
- 直接組合即可: f"求 ${derivative_symbols_latex}$"

示例：
✅ 正確：
    symbols = ' 與 '.join(_deriv_symbol_latex(order) for order in orders)
    q = f"已知 $f(x) = {poly_latex}$，求 ${symbols}$。"
    
❌ 錯誤：
    symbols = ' 與 '.join(_deriv_symbol_latex(order) for order in orders)
    q = f"已知 $f(x) = {poly_latex}$，求 ${symbols}$。"
    q = clean_latex_output(q)  # ❌ 會把 LaTeX 轉成 __LATEX_BLOCK_0__
```

---

## 💡 建議修復策略

### 策略 A: 最小修改（推薦用於科展）

1. **保持 BARE_PROMPT 不變**
   - 理由: 維持「真實用戶」對照組
   - 後果: Ab1 品質較差，但這正是我們要展示的

2. **修正 UNIVERSAL_GEN_CODE_PROMPT 的 Domain 函數說明**
   - 位置: `core/prompts/prompt_builder.py` 的 UNIVERSAL_GEN_CODE_PROMPT
   - 內容: 加入「Domain 函數輸出已含 LaTeX，不要再 clean」的明確指示

3. **讓 Ab3 的 Healer 自動修復 Ab1 類型的錯誤**
   - 保持 Ab1/Ab2 無 Healer（測試提示詞品質）
   - Ab3 展示 Healer 能救回多少問題

### 策略 B: 提升 Baseline（若需要更高品質的對照組）

1. **改進 BARE_PROMPT**
   - 加入字串格式化範例
   - 加入數學計算範例
   - 加入「純程式碼」要求

2. **同時修正 UNIVERSAL_GEN_CODE_PROMPT**

---

## 📈 實驗預期結果

### 當前狀態（手動修復後）：

| Ablation | Prompt Quality | Tools | Healer | 預期品質 | 實際品質 |
|----------|---------------|-------|--------|---------|---------|
| Ab1      | 簡陋 (Bare)    | 無     | 無      | 低 (60-70) | 93 (手動修復後) |
| Ab2      | 精密 (Engineered) | 有   | 無      | 高 (90-95) | 96 (手動修復後) |
| Ab3      | 精密 (同 Ab2) | 有     | 有      | 最高 (95-98) | 91 (自動修復) |

### 源頭修復後的預期：

| Ablation | Prompt Quality | 預期改善 |
|----------|---------------|---------|
| Ab1      | 簡陋 (保持不變) | 維持 60-70（這是設計目的） |
| Ab2      | 精密 (修復 Domain 說明) | → 95-97（避免 clean_latex_output 錯誤） |
| Ab3      | 精密 + Healer | → 95-98（Healer 修復剩餘問題） |

---

## ✅ 行動計劃

### 立即行動（針對 Ab2 Bug）：

1. **修改 `core/prompts/prompt_builder.py`**
   - 找到 UNIVERSAL_GEN_CODE_PROMPT 中的 Domain 函數說明區塊
   - 加入「不要對 Domain 函數輸出再呼叫 clean_latex_output」的警告

2. **測試修復效果**
   - 重新生成 Ab2: `python scripts/sync_skills_files.py` (選擇 Ablation 2)
   - 驗證不再出現 `__LATEX_BLOCK_` 佔位符

### 延後決策（針對 Ab1 Baseline）：

**討論問題**: Ab1 的 BARE_PROMPT 是否應該改進？

**選項 1: 保持簡陋 (推薦)**
- 優點: 真實反映用戶水平，凸顯 Ab2/Ab3 價值
- 缺點: Ab1 品質差，可能無法通過測試
- 適用: 研究重點是「提示工程 + Healer 的價值」

**選項 2: 適度改進**
- 優點: 獲得可用的 Baseline
- 缺點: 失去「真實用戶」對照意義
- 適用: 研究重點是「Healer 的邊際價值」

---

## 🔬 科展建議

對於科展報告，建議：

1. **實驗設計說明**
   - 明確說明 Ab1 使用「簡陋 Prompt」是刻意的實驗設計
   - 目的是模擬「一般用戶」的提示品質
   - 對照 Ab2 (工程化) 和 Ab3 (Healer) 的改善效果

2. **數據呈現**
   - Ab1 vs Ab2: 展示「提示工程」的價值
   - Ab2 vs Ab3: 展示「自癒機制」的邊際價值
   - Ab1 vs Ab3: 展示「完整系統」對簡陋輸入的容錯能力

3. **結論**
   - Prompt 工程可大幅提升品質 (Ab1 → Ab2: +X%)
   - Healer 機制可救回殘缺代碼 (Ab2 → Ab3: +Y%)
   - 綜合系統具備強韌性 (Ab1 → Ab3: +Z%)
