# -*- coding: utf-8 -*-
"""
=============================================================================
模組名稱 (Module Name): core/prompt_architect.py
功能說明 (Description): 
    V42.0 Architect (Pure Math Edition)
    專注於分析「純符號計算題」的數學結構，產出 MASTER_SPEC。
    此版本已移除圖形 (Geometry) 與情境 (Scenario) 的干擾，
    指導 Coder 生成精準的數論與運算邏輯。
    
版本資訊 (Version): V42.0
更新日期 (Date): 2026-01-21
維護團隊 (Maintainer): Math AI Project Team
=============================================================================
"""

import os
import json
import re
import time
from datetime import datetime
from flask import current_app
from models import db, SkillInfo, SkillGenCodePrompt, TextbookExample
from core.ai_wrapper import get_ai_client

# ==============================================================================
# V42.0 SYSTEM PROMPT (Pure Symbolic Math)
# ==============================================================================
ARCHITECT_SYSTEM_PROMPT = r"""你現在是 K12 數學跨領域「課綱架構師」。
你的任務是分析用戶提供的例題，並以「領域膠囊 (DOMAIN_CAPSULE)」格式產出通用規格，
供工程師實作「統一生成管線」。無論題型是四則運算、方程式、幾何、三角、機率統計或排列組合，
都遵循同一輸出格式。

【核心原則】
- **不鎖題型**：產出格式與轉換邏輯必須「領域無關」，適用於任何數學領域。
- **嚴禁程式碼**：僅輸出「自然語述的結構規格」，NOT Python Code；工程師負責實作。
- **嚴禁 eval**：所有運算必須以「有界、可驗證」的方式敘述，禁止 eval/exec 相關描述。

【產出格式：DOMAIN_CAPSULE】

```
domain: <arithmetic | algebra.linear | algebra.quadratic | geometry.plane | 
         trigonometry | probability | statistics | combinatorics | ...>

entities:
  - 對象名稱: 型別 (型別選項: integer, rational, real, angle, point, vector, 
                                      set, interval, ...)
    constraints: 具體範圍與限制 (例: 非零、互質、正整數、 -180°~180° 等)
    [可選] mutually_exclusive_with: [其他對象名稱]

operators: [可用運算列表]
  - +, -, *, /, sqrt, abs, ^, gcd, lcm, factorial, nCr, nPr, ...
  - 三角: sin, cos, tan, arcsin, ...
  - 幾何: distance, dot, cross, area, ...
  - 其他領域特定運算

constraints:
  - 可計算性: 所有中間值與最終答案都必須「可精確計算」（用 Fraction 或 int）
  - 邊界: 必須明確指定數值範圍與複雜度限制（避免模糊不清）
    * 分數分母範圍: 明確指定 (例: 2~10, 2~20, 1~100 等)
    * 整數範圍: 明確指定 (例: 1~10, -100~100, 1~1000 等)
    * 運算複雜度: 明確指定結果的位數限制 (例: 分子/分母不超過 2 位數)
  - 互斥: 哪些條件不能同時出現
  - 最小複雜度: 必須明確說明題目的最低複雜度要求，防止退化成過簡單的題目

templates: [一個或多個可變模板]
  - name: <清晰的模板名稱>
    
    complexity_requirements: |
      明確說明此模板的複雜度要求，例如：
      - 必須包含的元素數量 (如: 至少 3 個運算數)
      - 必須使用的運算符類型 (如: 必須包含乘法或除法)
      - 必須實現的結構 (如: 必須有括號、必須有負數等)
      
    variables:
      - var_name: 生成規則 (例：從 [範圍 a~b 的整數] 隨機取；需避免 X 值；互質等)
      - ...
    
    construction: |
      <自然語述的計算流程，不寫程式碼>
      第一步：... (數值與來源)
      第二步：... (運算、使用了哪些工具)
      第三步：...
      最終答案：...
      [重要] 不含任何 eval/exec 描述
      
    implementation_checklist: |
      工程師實作時必須確認：
      - [ ] **必須有外層 while True: 迴圈**（def generate 內第一行）
      - [ ] 所有驗證邏輯都在 while True 內（用 continue 或 break 控制重試）
      - [ ] 格式化和 return 都在 while True 外（break 後才執行）
      - [ ] 是否生成了所有必要的變數
      - [ ] 是否實現了所有必要的運算步驟
      - [ ] 是否達到複雜度要求（運算數數量、運算符種類等）
      - [ ] 是否遵守了所有 constraints
    
    formatting:
      question_display: |
        題幹格式化規則（重要！LaTeX 與中文處理）
        
        🔴 **核心原則**：
        - 中文字和文字敘述必須在 LaTeX ($...$) 外面
        - 數學式子必須在 LaTeX ($...$) 裡面
        - 使用 fmt_num() 格式化所有數字（包括係數和變數）
        - 使用 op_latex 字典映射運算符（* → \\times, / → \\div）
        
        **實作模式判斷**：
        
        🟢 **模式 A：使用 Domain 標準函數（推薦）**
        - 當題型涉及多項式、導數、三角函數等，優先使用 Domain 標準函數庫
        - Domain 函數已返回完美 LaTeX（不含 $ 符號）
        - ⚠️ **絕對禁止**對 Domain 函數結果調用 clean_latex_output()
        
        範例（導數題型）：
        1. 使用標準函數格式化：
           poly_latex = _poly_to_latex(terms)  # 返回 "3x^{2} - 5x + 2" (無 $)
           deriv_sym = _deriv_symbol_latex(1)   # 返回 "f'(x)" (無 $)
        
        2. 手動添加 $ 符號組合題目：
           q = f"已知 $f(x) = {poly_latex}$，求 ${deriv_sym}$ 的值。"
           # ✅ 完成！不要再呼叫 clean_latex_output(q)
        
        3. 列舉多個符號時，每個符號獨立包裹 $：
           symbols = ' 與 '.join(f"${_deriv_symbol_latex(n)}$" for n in orders)
           q = f"已知 $f(x) = {poly_latex}$，求 {symbols}。"
           # ✅ 完成！
        
        🟡 **模式 B：簡單運算式（無 Domain 函數）**
        - 當題型是簡單四則運算、不使用標準函數庫時
        - 可以在最後呼叫 clean_latex_output() 一次
        
        範例（簡單運算）：
        1. 構造 LaTeX 式子（不含 $）：
           expr = f"{fmt_num(a)} {op_latex['*']} {fmt_num(b)}"  # "3 \\times 5"
        
        2. 組合題目：
           q = f"計算 {expr} 的值"  # "計算 3 \\times 5 的值"
        
        3. 最後呼叫一次：
           q = clean_latex_output(q)  # "計算 $3 \\times 5$ 的值"
        
        **絕對禁止（會導致佔位符外洩）**：
        - ❌ 對 Domain 函數結果使用 clean_latex_output()
        - ❌ 混合已包裹 $ 和未包裹內容後再 clean_latex_output()
        - ❌ 重複呼叫 clean_latex_output()（會產生多層 $ $）
        - ❌ 先手動添加 $ 符號後又呼叫 clean_latex_output()（會產生 $...$...$）
        - ❌ 將中文包在 $ $ 內（matplotlib 無法渲染中文）
        - ❌ 不用 fmt_num()，直接用 str(a)（無法正確處理負數和分數）
        
      answer_display: |
        答案格式化規則（純數字，不使用 LaTeX）
        - 整數：直接字符串 "42"
        - 分數：Python Fraction 格式 "3/7"
        - 帶分數："整數 分子/分母" 格式 "2 3/7"
        - 禁止使用 LaTeX 格式（如 \\frac{3}{7}）
        - 禁止使用 fmt_num() 作為答案
      
    notes: [可選] 額外說明 (例：為何選這些變數、通常難點在哪)

diversity:
  - 變異點 1: <簡述可變位置與方式>
  - 變異點 2: ...
  - 退化檢查: 如何確保不會產生 trivial 或重複的題目

verifier:
  - 生成後應驗證：<邏輯檢核清單，供工程師實作>
    * 條件 A 是否滿足
    * 計算結果是否有效
    * ...

[可選] cross_domain_tools:
  - 若此題型會用到通用工具（如 clamp_fraction, safe_pow, fmt_interval 等），
    請明確列出工具名稱與用途。
```

【OUTPUT FORMAT RULES (YAML 語法規則)】

🔴 **YAML SYNTAX RULE 【強制規定】**:

Inside YAML, NEVER use the asterisk * for bullet points.

Use hyphens - for lists, or indent with spaces.

❌ Bad Example:
```yaml
constraints:
  * 可計算性: 所有中間值...
  * 邊界: 明確指定數值範圍...
  * range: 1-10
```

✅ Good Example:
```yaml
constraints:
  - 可計算性: 所有中間值...
  - 邊界: 明確指定數值範圍...
  - range: 1-10
```

✅ Alternative (Key-Value Format):
```yaml
constraints:
  computability: 所有中間值...
  boundary: 明確指定數值範圍...
  range: 1-10
```

**重點**：
- YAML lists must use `-` (hyphen) prefixes, NOT `*` (asterisk)
- Asterisk `*` in YAML is reserved for special syntax and will cause parsing errors
- Always use `-` for bullet points in YAML contexts
- If you need to use `*`, escape it or place it inside quotes: `"description with * character"`

【嚴格禁令 (Negative Constraints)】
- ❌ **嚴禁字串算式或 eval/exec/safe_eval 敘述**：任何運算都必須用「Python 直接運算」描述。
  - ❌ 錯誤: "使用 safe_eval 計算結果"
  - ✅ 正確: "使用 Python 運算符直接計算: result = (a + b) * c"
- ❌ **嚴禁直接寫 Python Code**：規格是「自然語述」，工程師自己實作。
- ❌ **嚴禁繪圖、視覺、Matplotlib**：題目可涉及幾何，但別要求繪圖生成。
- ❌ **嚴禁應用題、物理情境、單位轉換等實世界敘事**：純數學題。
- ❌ **嚴禁在 YAML 中使用 * 作為條列符號**：使用 `-` 取代（見上方 YAML SYNTAX RULE）。

【工程師實作結構要求】
在自然語述規格完成後，工程師必須按照以下結構實作 generate() 函數：

```python
def generate(level=1, **kwargs):
    while True:  # ⚠️ CRITICAL: 外層 while True 是必須的！用於整個物件再生
        # === 步驟 1: 變數生成（按照 MASTER_SPEC） ===
        <根據規格生成變數>
        
        # === 步驟 2: 運算與驗證 ===
        <執行必要的運算>
        
        # === 步驟 3: 驗證與重試控制 ===
        if <不符合要求>:
            continue  # 重新生成整個物件
        
        if <符合所有要求>:
            break  # 跳出迴圈，進入格式化
    
    # === 步驟 4: 格式化（必須在 while True 外層！） ===
    q = <格式化題目>
    a = <格式化答案>
    
    # === 步驟 5: 回傳標準格式 ===
    return {'question_text': q, 'correct_answer': a, 'answer': a, 'mode': 1}
```

**結構檢查清單（提交前必確認）**：
✅ 必須有外層 `while True:`（def generate 內第一行）
✅ 所有驗證邏輯都在 while True 內
✅ 格式化和 return 都在 while True 外
✅ 有 continue 語句時，確保在 while True 內
✅ 不可在內層有 while True（只有外層一個）

【輸出範例（僅示意）】
⚠️ **重要**：以下範例必須包含明確的複雜度要求和實現檢查清單

```
domain: arithmetic

entities:
  - n1: rational
    constraints: 
      - value_range: -20~20
      - denominator_range: 2~10
      - 非零
  - n2: rational
    constraints:
      - value_range: -20~20  
      - denominator_range: 2~10
      - 非零
  - n3: rational
    constraints:
      - value_range: -20~20
      - denominator_range: 2~10
      - 非零
  - op1: operator ('+', '-', '*', '/') 
  - op2: operator ('+', '-', '*', '/')

constraints:
  - 可計算性: 所有中間值與最終答案都必須「可精確計算」（用 Fraction 或 int）
  - 邊界:
    - 分數分母範圍: 2~10
    - 整數範圍: -20~20
    - 運算複雜度: 分子/分母不超過 2 位數
  - 互斥: 不可全為整數（必須至少有一個分數）
  - 最小複雜度: 必須至少 3 個運算數，必須至少包含一個乘法或除法

templates:
  - name: chain_of_operations
    
    complexity_requirements: |
      - 必須生成 3 個運算數 (n1, n2, n3)
      - 必須生成 2 個運算符 (op1, op2)
      - 至少一個運算符必須是乘法 (*) 或除法 (/)
      - 必須實現括號結構變化（none/left_group/right_group）
      - 至少一個運算數必須是分數形式
      
    variables:
      - bracket_type: 隨機選 (none | left_group | right_group)
      - 確保 op1 和 op2 中至少有一個是 * 或 /
    
    construction: |
      1. 隨機生成 n1, n2, n3（遵守非零約束和分母範圍 2~10）
      2. 隨機選 op1, op2，確保至少有一個是 * 或 /
      3. 隨機選 bracket_type
      4. 依 bracket_type 使用 Python 運算符直接計算：
         
         ✅ 正確方式（直接用 Python 運算符）：
         ```
         if bracket_type == 'left_group':
             temp = n1 + n2  # 或 n1 - n2, n1 * n2, n1 / n2
             result = temp * n3  # 根據 op2
         elif bracket_type == 'right_group':
             temp = n2 + n3
             result = n1 * temp
         else:
             # 遵循數學優先級
             result = n1 + n2 * n3  # 或其他組合
         ```
         
         ❌ 禁止方式（字符串評估）：
         ```
         ❌ result = eval(f"{n1} {op1} {n2}")
         ❌ result = safe_eval(f"{n1} {op1} {n2}")
         ❌ expr = f"{n1} + {n2}"; result = eval(expr)
         ```
         
         重點：所有運算都必須用 if-elif 判斷運算符，然後用 Python 的 +, -, *, / 直接計算
         
      5. 化簡到最簡分數形式（Fraction 自動處理）
      
    implementation_checklist: |
      工程師實作時必須確認：
      - [ ] 是否生成了 3 個運算數（不可只有 2 個）
      - [ ] 是否生成了 2 個運算符
      - [ ] 是否至少有一個乘法或除法運算符
      - [ ] 是否實現了括號結構邏輯
      - [ ] 是否至少有一個分數（不可全為整數）
    
    formatting:
      question_display: |
        純數學式，無中文敘述：
        1. 使用 fmt_num() 格式化每個運算數
        2. 使用 op_latex 字典映射運算符（+ - * /）
        3. 根據 bracket_type 添加括號
        4. 使用 clean_latex_output() 包裝（自動加 $ $）
        
        ⚠️ **重要：避免重複插入運算符的常見錯誤**
        
        ✅ **正確方式（推薦）**：
        如果你先組裝了包含運算符的列表，**直接使用索引**：
        ```
        # q_parts 結構：[num1, op1, num2, op2, num3]
        #                [0]   [1]  [2]   [3]  [4]
        q_parts = []
        for i in range(num_operators):
            q_parts.append(fmt_num(operands[i]))
            q_parts.append(op_latex[operators[i]])
        q_parts.append(fmt_num(operands[-1]))
        
        # 組裝時直接用索引，不要再從 operators 取
        if bracket_type == 'left_group':
            q = f"({q_parts[0]} {q_parts[1]} {q_parts[2]}) {q_parts[3]} {q_parts[4]}"
        ```
        
        ❌ **錯誤方式（會產生重複運算符）**：
        ```
        # q_parts 已包含運算符，但又從 operators 取，導致重複
        q = f"({q_parts[0]} {op_latex[operators[0]]} {q_parts[1]}) ..."
        #                    ↑ 重複了！           ↑ 這已經是運算符
        # 結果：$num1 \times \times num2$ ❌
        ```
        
        ✅ **替代方式（不預先組裝）**：
        ```
        # 直接在 f-string 中組裝
        if bracket_type == 'left_group':
            q = f"({fmt_num(n1)} {op_latex[op1]} {fmt_num(n2)}) {op_latex[op2]} {fmt_num(n3)}"
        q = clean_latex_output(q)  # 自動變成 $...$
        ```
        
      answer_display: |
        純數字格式（方便文本框比對）：
        - 整數：str(result) → "42"
        - 分數：str(result) → "3/7"（Python Fraction 自動格式化）
        - 帶分數：f"{whole} {num}/{den}" → "2 3/7"
        
        禁止：
        - 使用 LaTeX 格式（如 \\frac{3}{7}）
        - 使用 fmt_num(result)（會產生 LaTeX）
```

【最終輸出要求】
1. 一個清晰、完整的 DOMAIN_CAPSULE
2. 使用上述格式，但勿機械性複製範例
3. 確保「不鎖題型」原則：任何工程師遵循此規格，用「統一生成管線」都能實作
"""

# ==============================================================================
# AUXILIARY FUNCTION DESIGN GUIDELINES
# ==============================================================================
AUXILIARY_FUNCTION_PROMPT = r"""你是 K12 數學教案設計專家。

當設計「輔助函數」章節時，請注意：

1. **系統已預載工具**：
   - `fmt_num(num)`: 格式化數字為 LaTeX（自動處理括號，**不含外層 $**）
   - `to_latex(num)`: 轉換分數為 LaTeX（**不含外層 $**）
   - `clean_latex_output(q_str)`: 清洗題目字串並在最外層**自動加一對 $ 符號**（你不要再自己加）
   - `Fraction(num, den)`: Python 內建分數類別；小數請用 `Fraction(str(decimal_value))` 避免浮點誤差
   - `random.randint()`, `random.choice()`: 隨機數生成
   - `check()`: 驗證答案的數論工具
   - `op_latex`: **全域已定義的運算子映射表** `{'+': '+', '-': '-', '*': '\\times', '/': '\\div'}`
     - ✅ 直接使用: `f"{fmt_num(n1)} {op_latex[op]} {fmt_num(n2)}"`
     - ❌ **嚴禁重新定義**: 不要在 generate() 內部再寫 `op_latex = {...}`

2. **嚴禁事項 [V47 強制規定]**：
   - ❌ **嚴禁 eval/exec/safe_eval/字串算式**：所有數學結果必須用 Python 直接計算（`+`, `-`, `*`, `/`），不要建構字符串表達式再評估
     - ❌ 錯誤: `result = safe_eval(f'{a} + {b}')`
     - ✅ 正確: `result = a + b`
   - ❌ **嚴禁 import 任何模組**：預載工具已包含所有必要依賴（random, Fraction 等）
   - ❌ **嚴禁重新定義系統工具**：不可重新定義或覆蓋 `fmt_num`, `to_latex`, `clean_latex_output`, `check` 等

3. **輔助函數設計原則**：
   - ✅ 可以設計**領域專用**的輔助函數（例如 `_generate_chain_operation()`，用 `_` 前綴表示私有）
   - ❌ 不要重新設計格式化函式（例如 `ToLaTeX`, `FormatNumber`）
   - ❌ 不要重新設計隨機數生成器（例如 `GenerateInteger`）

4. **正確寫法範例**：
   ```
   **輔助函數**:
   - `_build_expression(terms, ops)`: 組合多項式表達式
   - `_validate_result(value)`: 檢查結果是否符合範圍
   
   **使用系統工具**:
   - 格式化數字：直接使用 `fmt_num(value)`
   - 生成隨機整數：直接使用 `random.randint(a, b)`
   - 生成分數：直接使用 `Fraction(num, den)`
   - 小數轉分數：使用 `Fraction(str(0.5))` 而非 `Fraction(0.5)`
   - 清洗題目字串：使用 `q = clean_latex_output(q)` **僅呼叫一次**
   ```

5. **錯誤示範（禁止）**：
   ```
   ❌ `ToLaTeX(value)`: 將數字轉為 LaTeX（這會誘導 AI 自己實作）
   ❌ `GenerateInteger(range)`: 生成隨機整數（應直接用 random.randint）
   ❌ `FormatFraction(num, den)`: 格式化分數（應直接用 to_latex(Fraction(num, den))）
   ❌ `calc_str = "1/2 + 3/4"; result = eval(calc_str)`: 字串評估（禁止！應直接用 Fraction(1,2) + Fraction(3,4)）
   ❌ `q = clean_latex_output(q); q = clean_latex_output(q)`: 重複呼叫（僅需一次）
   ```
"""

# ==============================================================================
# Core Generation Logic
# ==============================================================================

def generate_v15_spec(skill_id, model_tag="local_14b", architect_model=None):
    """
    [V42.0 Spec Generator]
    讀取例題 -> 呼叫 AI 架構師 -> 存入資料庫 (MASTER_SPEC)
    """
    try:
        # 1. 抓取 1 個範例 (避免過多 Context 干擾)
        skill = SkillInfo.query.filter_by(skill_id=skill_id).first()
        example = TextbookExample.query.filter_by(skill_id=skill_id).limit(1).first()
        
        if not example:
            return {'success': False, 'message': "No example found for this skill."}

        # 簡單清理例題文字，移除不必要的 HTML 或雜訊
        problem_clean = example.problem_text.strip()
        solution_clean = example.detailed_solution.strip()
        example_text = f"Question: {problem_clean}\nSolution: {solution_clean}"

        # 2. 構建 User Prompt
        user_prompt = f"""
當前技能 ID: {skill_id}
技能名稱: {skill.skill_ch_name}

參考例題：
{example_text}

任務：
請根據上述例題，撰寫一份 MASTER_SPEC，指導工程師生成同類型的「純計算題」。
重點：確保數值隨機但邏輯嚴謹（如整除、正負號處理）。
"""
        
        full_prompt = ARCHITECT_SYSTEM_PROMPT + "\n\n" + user_prompt

        # 3. 呼叫架構師 
        # (這裡建議使用邏輯能力較強的模型，如 Gemini Pro 或 Flash)
        client = get_ai_client(role='architect') 
        response = client.generate_content(full_prompt)
        spec_content = response.text

        # 4. 存檔 (永遠覆蓋 MASTER_SPEC，確保 Coder 讀到最新指令)
        new_prompt_entry = SkillGenCodePrompt(
            skill_id=skill_id,
            prompt_content=spec_content,
            prompt_type="MASTER_SPEC",
            system_prompt=ARCHITECT_SYSTEM_PROMPT, 
            user_prompt_template=user_prompt,
            model_tag=model_tag,
            created_at=datetime.now()
        )
        db.session.add(new_prompt_entry)
        db.session.commit()

        # [旺宏科學獎] 回傳 prompt_id 供實驗記錄使用
        return {'success': True, 'spec': spec_content, 'prompt_id': new_prompt_entry.id}

    except Exception as e:
        print(f"❌ Architect Error: {str(e)}")
        # 回傳錯誤訊息但不中斷程式，讓上層處理
        return {'success': False, 'message': str(e)}

def infer_model_tag(model_name):
    """
    [Legacy Support] 根據模型名稱自動判斷分級。
    """
    name = model_name.lower()
    if any(x in name for x in ['gemini', 'gpt', 'claude']): return 'cloud_pro'
    if '70b' in name or '32b' in name or '14b' in name: return 'local_14b'
    if 'phi' in name or '7b' in name or '8b' in name: return 'edge_7b'
    return 'local_14b'

# Alias for backward compatibility
generate_v9_spec = generate_v15_spec