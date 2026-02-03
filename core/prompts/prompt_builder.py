# -*- coding: utf-8 -*-
# ==============================================================================
# ID: core/prompts/prompt_builder.py
# Version: V2.3 (Added BARE_PROMPT_TEMPLATE for realistic user simulation)
# Last Updated: 2026-01-30
# Author: Math AI Research Team (Advisor & Student)
#
# [Description]:
#   Prompt 構建引擎 - 負責生成不同 Ablation 模式的 Prompt
#   [Research Edition] 用於消融研究實驗
#
# [Ablation Modes]:
#   1. BARE_PROMPT_TEMPLATE: 模擬一般用戶的 Prompt（Ab1 對照組）
#   2. UNIVERSAL_GEN_CODE_PROMPT: 完整規格書（Ab2/Ab3 實驗組）
#
# [Core Technology]:
#   - Template-based prompt generation
#   - Dynamic prompt assembly based on mode
#
# [Logic Flow]:
#   1. Input: (master_spec, mode, model_name)
#   2. Select Template based on mode
#   3. Inject MASTER_SPEC or Examples
#   4. Return final prompt string
# ==============================================================================

import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# [2026-01-30 新增] Ab1 Bare Prompt Template - 模擬一般用戶
# ==============================================================================
# 設計理念：
# - 模擬「一般老師」會如何跟 AI 下 Prompt
# - 使用自然語言，無工程化指導
# - 給 1-2 個參考例題，讓 AI 自己推理
# - 完全獨立於 UNIVERSAL_GEN_CODE_PROMPT 和 MASTER_SPEC
# ==============================================================================

BARE_PROMPT_TEMPLATE = """【角色設定】
你是一位中學數學老師的「出題助理」。

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
   - 'question_text': 題目文字
   - 'answer': 空字串 ''
   - 'correct_answer': 正確答案（必須是字串，例如："24" 或 "3x^2+5"；多個答案用換行分隔）
   - 'mode': 1

3. `check` 函式請回傳一個字典，包含：
   - 'correct': True 或 False
   - 'result': 回傳 '正確' 或 '錯誤'

4. 請使用 Python 的 standard library (如 random, math) 即可。

⚠️ 重要：只輸出 Python 程式碼！
- ✅ 正確：直接從 import 開始寫
- ❌ 錯誤：不要加任何說明文字或註解在程式碼之外
- ❌ 錯誤：不要在程式碼後面加「這個程式碼會...」的說明
- ❌ 錯誤：不要在程式碼後面加英文說明（如 "This code defines..."）
- ❌ 錯誤：不要用 ```python 包裹代碼
- ❌ 錯誤：不要加 Example usage 或 `if __name__ == '__main__'`
- ❌ 錯誤：不要加 Explanation/說明段落
- 🔴 CRITICAL：程式碼結束後不可有任何文字（包括空白行後的說明）
"""

# ==============================================================================
# [Fallback] BARE_MINIMAL_PROMPT - 保留作為備用
# ==============================================================================
# 注意：這個已被 BARE_PROMPT_TEMPLATE 取代，但保留以保持向後相容
# ==============================================================================

BARE_MINIMAL_PROMPT = r"""你是 Python 程式設計師。請根據以下 MASTER_SPEC 生成數學題目生成函數。

要求：
1. 實作函數：def generate(level=1, **kwargs)
2. ⚠️ 回傳字典格式（必須同時包含雙鍵）：
   return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
3. 只輸出 Python 代碼，不要有任何說明或 Markdown 標記

🔴 LaTeX 格式鐵律（必須遵守）：
   question_text 格式：
      ✅ 正確："計算 $(-3) + 5$ 的值"（中文在外，數學式用 $ $ 包裹）
      ✅ 正確："求 $2 \times (-4)$ 的結果"
      ❌ 錯誤："$(-3) + 5$"（缺少中文說明）
      ❌ 錯誤："計算$(-3) + 5$的值"（$ $ 與中文直接相連）
   
   answer 格式：
      ✅ 正確："42"（純數字）
      ✅ 正確："\frac{3}{7}"（LaTeX 分數，不含 $ $）
      ❌ 錯誤："答案是 42"（不要加中文說明）

📐 題目字串拼接範例（3步驟標準流程）：
   # 步驟1: 先拼接數學式（不含 $ $）
   math_expr = f"{fmt_num(n1)} {op_latex['+']} {fmt_num(n2)}"
   
   # 步驟2: 組合中文與數學式（手動加 $ $）
   q = f"計算 ${math_expr}$ 的值"  # ⚠️ 使用簡短變量名 q
   
   # 步驟3: 最後呼叫 clean_latex_output()（可選，用於進階清洗）
   q = clean_latex_output(q)
   
   # 步驟4: 格式化答案為純數字字符串
   a = str(answer)  # ⚠️ 使用簡短變量名 a
   
   # ⚠️ 返回格式（必須完全遵守）：
   return {
       'question_text': q,
       'correct_answer': a,
       'answer': a,         # ⚠️ CRITICAL: 必須同時包含此鍵（與 correct_answer 值相同）
       'mode': 1
   }

❌ 常見錯誤（絕對不要這樣寫）：
   # 錯誤1: 在 f-string 內呼叫 clean_latex_output()
   q_str = f"計算 {clean_latex_output(expr)} 的值"  # ❌ 錯誤
   
   # 錯誤2: 字串拼接時用 + 運算符混合函式呼叫
   q_str = f"計算 {clean_latex_output(fmt_num(n1) + op_latex['*'] + fmt_num(n2))} 的值"  # ❌ 錯誤
   
   # 錯誤3: 只返回單一 answer 鍵
   return {'question_text': q, 'answer': a, 'mode': 1}  # ❌ 缺少 'correct_answer'
   
   # 錯誤4: 變量名過長
   question_text = "..."  # ❌ 應使用 q
   answer = "..."         # ❌ 應使用 a

📐 使用以下工具函數（已預先定義）：
   - fmt_num(x): 格式化數字（負數自動加括號）
   - op_latex: 運算符映射字典 {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
   - clean_latex_output(q_str): 自動清洗 LaTeX 格式（僅用於最後一步）

提示：你可以使用 Python 的 random, math, Fraction 等標準庫。
"""

# ==============================================================================
# [V2.4 NEW] SIMPLIFIED_GEN_CODE_PROMPT - 簡化版工程化 Prompt（鷹架法）
# ==============================================================================
# 設計理念：
# - 基於教學脚手架原則：清楚的任務 → 提供的工具 → 簡潔的規則 → 成功範例
# - 從 9000+ 字符的 UNIVERSAL_GEN_CODE_PROMPT 簡化到 ~2000 字符
# - 只保留 5 條不可違反的核心規則，移除冗餘警告符號
# - 讓 Qwen 專注在核心任務，降低認知負荷
# ==============================================================================

SIMPLIFIED_GEN_CODE_PROMPT = r"""【角色】K12 數學演算法工程師

【任務】
實作 `def generate(level=1, **kwargs)` 函數，根據 MASTER_SPEC 生成數學問題的完整 Python 代碼。
該函數應返回 dict: {'question_text': str, 'correct_answer': str, 'answer': str, 'mode': 1}

【預載工具】(直接使用，無需定義)
- 模塊: random, math, re, ast, operator, os, Fraction
- 工具函數: fmt_num(n), to_latex(n), clean_latex_output(q), check(user_answer, correct_answer)
- 多項式工具: _coeffs_to_terms(coeffs), _poly_to_latex(terms), _poly_to_plain(terms), _differentiate_poly(terms, order=1), _deriv_symbol_latex(order)
- 其他: op_latex, is_prime, gcd, lcm, get_factors, nCr, nPr, factorial_bounded, clamp_fraction, safe_pow, rational_gauss_solve

【核心規則】(只有 5 條，最重要的)

1. ✅ **安全的迴圈設計 + 數學一致性約束**
   - 集合選擇必須遵守 **num_terms ≤ (max_degree + 1)** 的物理極限
     * 例：degree 3 有 4 個可能指數 [0,1,2,3]，所以 num_terms ≤ 4
     * 例：度數 5 有 6 個可能指數，所以 num_terms ≤ 6
     * 使用 `num_terms = random.randint(3, min(5, max_degree + 1))` 確保合法性
   - 使用 shuffle + slice：`available = list(range(n)); random.shuffle(available); selected = available[:k]`
   - 外層 while True 只用於整個物件再生，內層絕對不能有無終止條件迴圈
   - 若違反此約束，會導致 while 迴圈無限尋找不重複元素而卡死

2. ✅ **LaTeX 格式**（只有一條簡單規則）
   - 所有數學式必須被 $ 包裹：f"計算 ${expr}$ 的值"
   - **中文與 $ 必須分離**：f"求 ${expr}$ 的因式分解"（**不是** f"求${expr}$的"）

3. ✅ **答案格式**（嚴格要求）
   - 純結果，不含符號、等號、LaTeX
   - ✅ 正確（多個答案用換行分隔）：
     ```
     6x^2-10x
     12x-10
     ```
   - ❌ 錯誤（含函數符號和等號）：
     ```
     f'(x) = 6x^2-10x
     f''(x) = 12x-10
     ```
   - **答案欄位不含 $ 符號**（純文字）

4. ✅ **Domain 函數使用**
   - 先轉換格式：terms = _coeffs_to_terms(coeffs)
   - 再調用函數：_poly_to_latex(terms), _differentiate_poly(terms), _poly_to_plain(terms)
   - 不要對結果呼叫 clean_latex_output()

5. ✅ **只輸出代碼**
   - 不要在代碼結尾加說明或註解
   - 不使用 eval/exec/safe_eval


【成功的代碼模式】

```python
def generate(level=1, **kwargs):
    # 步驟 1: 生成參數（數學一致性約束）
    max_degree = random.randint(3, 5)
    # 確保項數不超過物理極限 (degree 3 → 4項，degree 5 → 6項)
    # num_terms 必須 ≤ (max_degree + 1)
    max_possible_terms = max_degree + 1
    num_terms = random.randint(3, min(5, max_possible_terms))
    
    # 步驟 2: 生成係數
    coeffs = [random.randint(-10, 10) for _ in range(num_terms)]
    while coeffs[0] == 0:
        coeffs[0] = random.randint(1, 10)
    
    # 步驟 3: 使用 shuffle + slice（安全集合選擇）
    available_exponents = list(range(max_degree + 1))
    random.shuffle(available_exponents)
    selected_exponents = available_exponents[:num_terms]
    
    # 步驟 4: 轉換為 terms 格式
    terms = [(coeffs[i], selected_exponents[i]) for i in range(num_terms)]
    
    # 步驟 5: 計算導數
    deriv1_terms = _differentiate_poly(terms, order=1)
    deriv2_terms = _differentiate_poly(terms, order=2)
    
    # 步驟 6: 組裝題目（手動加 $，中文與 $ 分離）
    poly_latex = _poly_to_latex(terms)
    q = f'已知 $f(x) = {poly_latex}$ ，求 $f\'(x)$ 與 $f\'\'(x)$ 。'
    
    # 步驟 7: 組裝答案（純多項式，換行分隔，無 LaTeX、無函數符號）
    ans1 = _poly_to_plain(deriv1_terms)
    ans2 = _poly_to_plain(deriv2_terms)
    a = f"{ans1}\n{ans2}"  # 多個答案用換行分隔
    
    return {
        'question_text': q,
        'correct_answer': a,
        'answer': a,
        'mode': 1
    }
```
"""

# ==============================================================================
# 完整的 UNIVERSAL_GEN_CODE_PROMPT（194 行完整版）
# ==============================================================================

UNIVERSAL_GEN_CODE_PROMPT = r"""【角色】K12 數學演算法工程師。
【任務】實作 `def generate(level=1, **kwargs)`，根據 MASTER_SPEC 產出完整的 Python 代碼。
【限制】
1. 僅輸出代碼，無 Markdown/說明
2. **嚴禁 eval/exec/safe_eval**
3. 🔴 **禁止在代碼結尾加任何說明文字或註解段落**
   - ❌ 錯誤：代碼後直接寫 "This implementation follows..." 或中文說明
   - ✅ 正確：代碼結束後不加任何文字
4. 🔴 **禁止 Example usage / __main__ 測試段落**
    - ❌ 錯誤：`if __name__ == '__main__': ...`
    - ❌ 錯誤：`### Explanation:` 或任何說明段落

🔴 **最高優先級：MASTER_SPEC 是唯一權威來源**
- 你收到的 MASTER_SPEC 包含完整的題型定義、複雜度要求和實現檢查清單
- **必須逐項實現 MASTER_SPEC 中的所有要求**
- 任何與 MASTER_SPEC 衝突的通用規則都應以 MASTER_SPEC 為準

🔴 **【CRITICAL】集合選擇的強制規則 - 違反將導致無限迴圈！**
- ❌ 嚴禁使用 `while True` + `if not in set` 模式生成不重複隨機元素
  ```python
  ❌ 危險模式（會導致無限迴圈）：
  while True:
      exp = random.randint(0, max_degree)
      if exp not in exponents:
          exponents.add(exp)
          break
  ```
- ✅ 必須使用 **shuffle + slice 模式**（唯一正確方式）：
  ```python
  ✅ 正確模式（O(n)，絕對不會無限迴圈）：
  max_degree = random.randint(3, 5)
  num_terms = random.randint(3, min(5, max_degree + 1))  # 關鍵：num_terms ≤ max_degree + 1
  available = list(range(max_degree + 1))
  random.shuffle(available)
  selected = available[:num_terms]
  ```
- 原因：如果 num_terms > max_degree + 1，while 迴圈無法找到足夠多的不重複元素，導致程式卡死

【預載工具 (直接使用)】
- random, math, re, ast, operator, os, Fraction
- fmt_num(n), to_latex(n), clean_latex_output(q)
- check(user_answer, correct_answer)
- op_latex = {'+': '+', '-': '-', '*': '\\times', '/': '\\div'}
- 數論函數: is_prime(n), gcd(a,b), lcm(a,b), get_factors(n)
- 組合數學: nCr(n,r), nPr(n,r), factorial_bounded(n)
- 其他: clamp_fraction(f), safe_pow(base,exp), rational_gauss_solve(...)

【函數使用規則（CRITICAL）】
- 只使用已提供的 helper 名稱與原始參數簽名，**不可臆造新函數**。
- ❌ 錯誤：`_poly_to_string(...)`, `_deriv_symbol_latex(order, latex=False)`
- ✅ 正確：`_poly_to_latex(terms)`, `_poly_to_plain(terms)`, `_deriv_symbol_latex(order)`, `_deriv_symbol_plain(order)`
- 若手上是係數列表，先用 `_coeffs_to_terms(coeffs)` 轉成 `[(c,e), ...]` 再丟給 `_poly_to_latex/_poly_to_plain`。

【生成管線標準】
1. **結構要求**：必須有外層 `while True:` 迴圈（用於物件再生）
2. 變數生成（嚴格遵守 MASTER_SPEC）
3. 運算（Python 直接計算，嚴禁 eval）
4. 運算順序與括號
5. 題幹格式化（LaTeX + 中文處理）
6. 答案格式化
7. 回傳標準格式

【安全生成範例 - 請參照此模式】
```python
def generate(level=1, **kwargs):
    while True:  # ⚠️ CRITICAL: 外層 while True 是必須的！用於整個物件再生
        # 步驟 1: 使用 shuffle + slice 選擇集合元素（絕對安全）
        max_degree = random.randint(3, 5)
        num_terms = random.randint(3, min(5, max_degree + 1))  # 關鍵：確保不超過可選值數量
        
        # 步驟 2: 實際變數生成
        available_degrees = list(range(max_degree + 1))
        random.shuffle(available_degrees)
        selected_degrees = available_degrees[:num_terms]  # 直接切片，O(1) 時間
        
        # 步驟 3: 生成基礎物件
        poly_terms = []
        for d in selected_degrees:
            coeff = random.randint(-10, 10)
            while coeff == 0:  # 小範圍 while 可接受（只是避免 0）
                coeff = random.randint(-10, 10)
            poly_terms.append((coeff, d))
        
        # 步驟 4: 驗證並決定是否重試
        deriv = differentiate(poly_terms)
        if is_valid(deriv):  # 如果有效則跳出
            break
        # 否則 continue，回到 while True 開頭重新生成整個物件
    
    # 步驟 5: 生成答案（CRITICAL：答案只包含結果，不含符號前綴或等號，多個答案用換行分隔）
    # ✅ 正確範例（求導數題型）：
    ans_parts = []
    for order in derivative_orders_list:
        deriv_terms = _differentiate_poly(base_poly_terms, order=order)
        poly_plain = _poly_to_plain(deriv_terms)  # 只取多項式文字
        ans_parts.append(poly_plain)  # 不加 "f'(x) =" 前綴
    
    correct_answer = '\n'.join(ans_parts)  # 換行分隔
    # 結果：
    # 2
    # 0
    # 而非 "f''(x) = 2\nf^(3)(x) = 0" 或 "2, 0"
    
    # ❌ 錯誤範例（會導致評分失敗）：
    # ans_parts.append(f"{_deriv_symbol_plain(k)} = {poly_plain}")  # 包含等號
    # correct_answer = ', '.join(ans_parts)  # 用逗號分隔（舊格式）
    
    # 步驟 6: 格式化題幹與返回
    q = f'...'
    return {'question_text': q, 'correct_answer': correct_answer, 'answer': correct_answer, 'mode': 1}
```

⚠️ **返回格式檢查清單（CRITICAL - 違反將導致驗證失敗）**

1. **必須返回字典**，不是 tuple：
   - ✅ 正確：`return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}`
   - ❌ 錯誤：`return q, a`（這是 tuple，不是字典！）
   - ❌ 錯誤：`return (q, a)`（同樣是 tuple）

2. **字典必須包含以下 4 個 key**（缺一不可）：
   - `'question_text'`: 題目字串
   - `'correct_answer'`: 答案字串（純文本，不是字典！）
   - `'answer'`: 同 `'correct_answer'`
   - `'mode'`: 固定值 1

3. **correct_answer 必須是字串**，不是字典：
   - ✅ 正確：`'correct_answer': '24\n4x^3+14x'`（換行分隔的字串）
   - ❌ 錯誤：`'correct_answer': {'f\'(x)': ..., 'f\'\'(x)': ...}`（字典）
   - ❌ 錯誤：`'correct_answer': ['24', '4x^3+14x']`（列表）

🔴 **【CRITICAL】答案格式強制規則 - 違反將導致評分失敗！**

**核心原則**：正確答案 = 純數學運算結果，學生在文本框中直接輸入（不含函數符號、等號、LaTeX）

1. **單個答案格式**（求 1 個值）：
   ```python
   ✅ 正確: correct_answer = '36x^2 + 10'  # 純多項式
   ✅ 正確: correct_answer = '42'           # 純數字
   ✅ 正確: correct_answer = '3/7'          # 純分數
   ❌ 錯誤: correct_answer = 'f\'(x) = 36x^2 + 10'      # 不要包含函數符號和等號
   ❌ 錯誤: correct_answer = '$36x^2 + 10$'             # 不要包含 LaTeX 符號 $ $
   ❌ 錯誤: correct_answer = r'36x^{{2}} + 10'          # 不要包含 LaTeX 大括號
   ```

2. **多個答案格式**（求 2 個或以上的值，例如求導函數）：
   ```python
   ✅ 正確: correct_answer = '36x^2 + 10\n72x'         # 換行分隔
   ✅ 正確: correct_answer = '24\n12\n6'               # 多個數字
   ✅ 正確: correct_answer = '3/7\n5/8\n1/2'           # 多個分數
   ❌ 錯誤: correct_answer = 'f\'(x) = 36x^2 + 10\nf\'\'(x) = 72x'    # 不要含函數符號
   ❌ 錯誤: correct_answer = 'f\'(x) = 36x^2 + 10, f\'\'(x) = 72x'   # 不要含函數符號
   ❌ 錯誤: correct_answer = '36x^2 + 10, 72x'                       # 不要用逗號分隔
   ```

3. **為什麼**：換行分隔讓系統自動判斷學生輸入的多個答案：
   - ✅ 學生可輸入：`36x^2 + 10`（第一個答案）
   - ✅ 系統自動匹配：第一個答案=`36x^2 + 10`✓，第二個答案=`72x`✓
   - ❌ 無法輸入：`f'(x) = 36x^2 + 10` （沒有鍵盤輸入 f'(x) = 符號）

【結構檢查清單 - 提交代碼前必須確認】
✅ **必須有外層 `while True:`**（def generate 內第一行）
✅ **所有驗證邏輯都在 while True 內**
✅ **格式化和 return 都在 while True 外**
✅ **有 continue 語句時，確保在 while True 內**
✅ **不可在內層有 while True**（只有外層一個）
✅ **必須返回字典**（不是 tuple）
✅ **字典必須有 4 個 key**（question_text, correct_answer, answer, mode）
✅ **correct_answer 必須是字串**（不是字典或列表）
✅ **correct_answer 只包含純數學式**（無函數符號、無等號、無 LaTeX 符號）
✅ **多答案必須用換行分隔**（'\n' 換行分隔，不用逗號）


【LaTeX 格式鐵律 - 方案 1：場景區分法】(CRITICAL - 違反此規則將導致顯示錯誤)

🎯 **核心原則**：工程化 = 簡潔直接，不是複雜的字串處理

📋 **場景分類決策樹**：
```
你的題型使用了 Domain 標準函數嗎？（如 _poly_to_latex, _deriv_symbol_latex 等）
    │
    ├─ ✅ 是 → 🟢 場景 A：Domain 函數題型
    │          → 手動添加 $ 符號
    │          → 🔴 絕對禁止 clean_latex_output()
    │
    └─ ❌ 否 → 🟡 場景 B：簡單運算題型
               → 手動添加 $ 符號（推薦）
               → 或最後調用一次 clean_latex_output()（可選）
```

---

## 🟢 場景 A：Domain 函數題型（多項式、導數、三角等）

### ✅ 標準實作流程（方案 1）

```python
# 步驟 1: 使用 Domain 函數格式化（返回不含 $ 的完美 LaTeX）
poly_latex = _poly_to_latex(base_poly_terms)  # "10x^{5} + 9x^{2} + 5"

# 步驟 2: 手動為每個數學符號添加 $ $
derivative_symbols_latex = ' 與 '.join(
    f"${_deriv_symbol_latex(order)}$" 
    for order in derivative_orders_list
)
# 結果: "$f^{(3)}(x)$ 與 $f^{(4)}(x)$"

# 步驟 3: 組合題目（直接使用 f-string）
q = f"已知 $f(x) = {poly_latex}$，求 {derivative_symbols_latex}。"
# 最終: "已知 $f(x) = 10x^{5} + 9x^{2} + 5$，求 $f^{(3)}(x)$ 與 $f^{(4)}(x)$。"

# ✅ 完成！不需要也不應該呼叫 clean_latex_output()
```

### 🔴 絕對禁止的錯誤用法

```python
# ❌ 錯誤 1: 混合已包裹和未包裹的內容
poly_latex = _poly_to_latex(terms)
deriv_sym = _deriv_symbol_latex(1)  # 無 $ $
q = f"已知 $f(x) = {poly_latex}$，求 {deriv_sym}。"  # 混合了
q = clean_latex_output(q)  # 💣 炸了！產生 placeholder 外洩

# ❌ 錯誤 2: 對 Domain 函數結果使用 clean_latex_output()
poly_latex = _poly_to_latex(terms)
q = f"已知 $f(x) = {poly_latex}$，求導數。"
q = clean_latex_output(q)  # 💣 多此一舉，可能破壞結果

# ❌ 錯誤 3: 寫自己的清洗函數
def my_clean_function(s):  # 💣 不要這樣做！
    # 複雜的 regex 替換邏輯...
    return result
```

### 📌 記憶口訣
```
Domain 函數已完美 → 手動加 $ → 直接用，不 clean
```

---

## 🟡 場景 B：簡單運算題型（四則運算、不使用 Domain 函數）

### ✅ 方式 A：手動添加 $（推薦 - 最簡潔）

```python
# 步驟 1: 構造數學式（不含 $ $）
expr = f"{fmt_num(a)} {op_latex['*']} {fmt_num(b)}"  # "3 \\times 5"

# 步驟 2: 手動添加 $ 符號
q = f"計算 ${expr}$ 的值"  # "計算 $3 \\times 5$ 的值"

# ✅ 完成！簡單直接
```

### ✅ 方式 B：使用 clean_latex_output()（可選）

```python
# 步驟 1: 構造數學式（不含 $ $）
expr = f"{fmt_num(a)} {op_latex['*']} {fmt_num(b)}"  # "3 \\times 5"

# 步驟 2: 組合題目（不加 $）
q = f"計算 {expr} 的值"  # "計算 3 \\times 5 的值"

# 步驟 3: 最後調用一次 clean_latex_output()
q = clean_latex_output(q)  # "計算 $3 \\times 5$ 的值"

# ✅ 也可以，但方式 A 更簡潔
```

### 📌 記憶口訣
```
簡單運算 → 優先手動 $ → 或最後 clean 一次
```

---

## 🔴 絕對禁止的混合模式（會導致 placeholder 外洩）

```python
# 💣 致命組合：Domain 函數 + 混合內容 + clean_latex_output()
poly_latex = _poly_to_latex(terms)                    # Domain 函數
deriv_sym = _deriv_symbol_latex(1)                     # Domain 函數
q = f"已知 $f(x) = {poly_latex}$，求 {deriv_sym}。"   # 混合了 $ 和裸露內容
q = clean_latex_output(q)                              # 💣 爆炸！

# 結果: "已知 __ $LATEX$ _ $BLOCK$ _ $0$ __，求 $f$ ^{ $(1)$ } $(x)$..."
```

---

## 📊 通用規則（適用所有場景）

1. **數學表達式必須用 $ $ 包裹**
   ✅ 正確：f"計算 ${fmt_num(a)} + {fmt_num(b)}$ 的值"
   ❌ 錯誤：f"計算 {fmt_num(a)} + {fmt_num(b)} 的值"  # 缺少 $

2. **中文與 $ $ 必須分離**
   ✅ 正確：f"求 ${expr}$ 的因式分解"
   ❌ 錯誤：f"求${expr}$的因式分解"  # $ 與中文相連

3. **優先使用簡單的 f-string**
   - ✅ 推薦：f"已知 ${poly_latex}$，求 ${deriv_sym}$。"
   - ⚠️ 可選：先拼接再 clean_latex_output()（僅限場景 B）
   - ❌ 禁止：寫複雜的佔位符替換邏輯

4. **工程化 = 簡潔，不是複雜**
   - ✅ 好的工程化：清晰的變數命名、直接的 f-string
   - ❌ 壞的工程化：過度複雜的字串處理、多層替換邏輯

【題幹 LaTeX 拼接規則（CRITICAL）】
1. **多個符號必須分別包 $**，不可整段包在 $$ 或混用
    - ✅ 正確：`symbols = ' 與 '.join(f"${_deriv_symbol_latex(n)}$" for n in orders)`
    - ✅ 正確：`q = f"已知 $f(x) = {poly_latex}$，求 {symbols}。"`
    - ❌ 錯誤：`q = f"... 求 $${symbols}$$。"`（會產生 $$）
2. **已手動加 $ 的內容，絕對不可再做整段包裹或 clean_latex_output**
    - ❌ 錯誤：`q = clean_latex_output(q)`（若 q 內已有 $...$）


【無限迴圈與邏輯安全鐵律】(CRITICAL - 違反將導致系統卡死)

� **必須使用的結構（REQUIRED）**

1. **外層 `while True:` 是必須的**
   - ✅ **必須有**：`def generate` 的第一行必須是 `while True:`
   - 用途：用於整個物件再生（驗證失敗時重新生成）
   - 結構：
     ```python
     def generate(level=1, **kwargs):
         while True:  # ⚠️ 必須！外層物件再生迴圈
             # 步驟 1: 生成變數
             # 步驟 2: 驗證
             if <不符合要求>:
                 continue  # 重新生成
             break  # 符合要求，跳出
         
         # 格式化（在 while True 外層）
         return {...}
     ```

🔴 **絕對禁止使用的危險模式**

2. **禁止內層無限迴圈**
   - ❌ **絕對禁止**：在 `while True:` **內部**再用 `while True:` 或其他無保證終止的迴圈
   - ❌ **絕對禁止**：`while len(set) < target:` 如果 target 超過可選值數量
   - 原因：沒有保證終止條件，容易導致無限迴圈卡死
   
   範例（會卡死）：
   ```python
   def generate(level=1, **kwargs):
       while True:  # ✅ 外層可以
           # ❌ 錯誤！內層又有無限迴圈
           degrees = set()
           while len(degrees) < num_terms:  # 可能永遠湊不滿
               degree = random.randint(0, max_degree)
               degrees.add(degree)
   ```

✅ **安全的內層實作模式（必須使用）**

1. **使用 Shuffle + Slice 模式（推薦）**
   ```python
   # ✅ 正確：保證在 O(n) 時間內完成，絕對不會無限迴圈
   max_degree = random.randint(3, 5)
   num_terms = random.randint(3, min(5, max_degree + 1))  # 確保 num_terms <= 可選值數量
   
   available_degrees = list(range(max_degree + 1))
   random.shuffle(available_degrees)
   selected_degrees = available_degrees[:num_terms]  # 直接切片，保證成功
   ```

2. **使用有限重試的 while 迴圈（只在必要時）**
   ```python
   # ✅ 正確：有明確的最大重試次數
   while True:
       # 生成邏輯
       poly = generate_polynomial()
       deriv = differentiate(poly)
       
       # 驗證
       if is_valid(deriv):
           break  # 成功則退出
   ```
   
   **注意**：外層 `while True` 只在整個物件再生時使用，內層絕對不可以有無限迴圈！

3. **數據一致性**
   - 在重試時，務必清空或重置相關的列表，避免保留上一次失敗的殘留數據。
   - ✅ 正確：每次重試前執行 `results = []`（清空）
   - ❌ 錯誤：在外層定義 `results = []`，內層 `continue` 時不清空

【函式實作檢查清單】
□ **def generate(level=1, **kwargs)** 存在
□ **安全集合選擇**: 是否使用了 shuffle + slice 模式？（避免無限迴圈）
□ **LaTeX Formatting**: 所有數學符號（包括列表中的符號）是否都有 `$` 包裹？
□ **No Double Cleaning**: 是否避免了對 Domain 函數結果使用 clean_latex_output？
□ **答案格式**: 是否只包含結果（等號右邊），不含符號前綴？
□ **答案分隔**: 多個答案是否用逗號分隔（不是換行）？
□ **答案欄位不含 $ $ 符號**
□ **回傳格式**: {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}


"""


class PromptBuilder:
    """
    Prompt 構建引擎 - 負責生成不同 Ablation 模式的 Prompt
    
    支援 3 種 Ablation 模式：
    - Ab1: BARE_PROMPT_TEMPLATE (一般用戶自然語言 Prompt)
    - Ab2: SIMPLIFIED_GEN_CODE_PROMPT + MASTER_SPEC (工程化鷹架版，~2000 字符)
    - Ab3: SIMPLIFIED_GEN_CODE_PROMPT + MASTER_SPEC + Healer (鷹架版 + AST 修復)
    """
    
    @staticmethod
    def build(master_spec: str, ablation_id: int = 3, textbook_example: str = "", topic: str = "", skill_id: str = "") -> str:
        """
        構建 Prompt（[V47.13] 新增 Domain 函數庫自動注入）
        
        Args:
            master_spec: MASTER_SPEC 字串
            ablation_id: Ablation 模式 ID (1, 2, 3)
            textbook_example: [Ab1 專用] 教科書範例文字
            topic: [Ab1 專用] 題目主題（從 skill_id 提取）
            skill_id: [V47.13 新增] 用於自動識別所需 Domain 函數庫
            
        Returns:
            str: 完整的 Prompt（已自動注入 Domain 標準函數）
        """
        # [V47.13] 自動識別並注入 Domain 函數庫
        domain_injection = ""
        if skill_id:
            try:
                from core.prompts.domain_function_library import get_required_domains, get_domain_helpers_code
                required_domains = get_required_domains(skill_id)
                if required_domains:
                    domain_code = get_domain_helpers_code(required_domains)
                    domain_injection = f"""

### 🔧 標準函數庫（{', '.join(required_domains)}）

{domain_code}

⚠️ 規則：
1. 直接調用上述函數，禁止重新定義
2. 你只需實現 `def generate(level=1, **kwargs)`
3. 答案格式：純多項式換行分隔，例 "6x-5\n6"（禁止包含 f'(x)= 或逗號）
"""
                    logger.info(f"   ✅ Domain 函數庫注入: {required_domains}")
            except Exception as e:
                logger.warning(f"   ⚠️ Domain 函數庫注入失敗: {e}")
        
        if ablation_id == 1:
            # Ab1: 模擬一般用戶的 Prompt + 範例 + 主題
            # 如果沒有提供範例，使用預設範例
            if not textbook_example:
                textbook_example = "範例：計算 3 + 5 = ?"
            if not topic:
                topic = "數學題目"
            
            prompt = BARE_PROMPT_TEMPLATE.format(
                topic=topic,
                textbook_example=textbook_example
            )
            logger.info(f"Prompt Ab1 - BARE_PROMPT_TEMPLATE (自然語言)")
            logger.info(f"   Topic: {topic}")
            logger.info(f"   Bare Prompt: {len(BARE_PROMPT_TEMPLATE)} chars")
            logger.info(f"   Textbook Example: {len(textbook_example)} chars")
            logger.info(f"   Final Prompt: {len(prompt)} chars")
        elif ablation_id == 2:
            # Ab2: SIMPLIFIED Prompt (鷹架版) + MASTER_SPEC + Domain 函數庫
            prompt = SIMPLIFIED_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{master_spec}"
            logger.info(f"Prompt Ab2 - SIMPLIFIED_GEN_CODE_PROMPT + MASTER_SPEC + Domain (鷹架版)")
            logger.info(f"   Simplified Prompt: {len(SIMPLIFIED_GEN_CODE_PROMPT)} chars")
            logger.info(f"   Domain Injection: {len(domain_injection)} chars")
            logger.info(f"   MASTER_SPEC: {len(master_spec)} chars")
        else:
            # Ab3 (默認): SIMPLIFIED Prompt (鷹架版) + MASTER_SPEC + Domain 函數庫
            prompt = SIMPLIFIED_GEN_CODE_PROMPT + domain_injection + f"\n\n### MASTER_SPEC:\n{master_spec}"
            logger.info(f"Prompt Ab{ablation_id} - SIMPLIFIED_GEN_CODE_PROMPT + MASTER_SPEC + Domain (鷹架版)")
            logger.info(f"   Simplified Prompt: {len(SIMPLIFIED_GEN_CODE_PROMPT)} chars")
            logger.info(f"   Domain Injection: {len(domain_injection)} chars")
            logger.info(f"   MASTER_SPEC: {len(master_spec)} chars")
        
        return prompt
    
    @staticmethod
    def get_skeleton() -> str:
        """
        獲取代碼框架（用於向後兼容）
        
        Returns:
            str: 空字串（CALCULATION_SKELETON 已棄用）
        """
        return ""


# 導出常量（向後兼容）
__all__ = [
    'PromptBuilder',
    'BARE_PROMPT_TEMPLATE',
    'BARE_MINIMAL_PROMPT',
    'UNIVERSAL_GEN_CODE_PROMPT',
    'SIMPLIFIED_GEN_CODE_PROMPT',
]
