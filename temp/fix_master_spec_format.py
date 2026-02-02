#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修復 MASTER_SPEC - 添加格式轉換和答案格式範例"""
import sqlite3
import sys

skill_id = 'gh_ApplicationsOfDerivatives'

# 新的 MASTER_SPEC (在原有基礎上添加關鍵範例)
NEW_MASTER_SPEC = """```
domain: algebra.polynomial.derivatives

entities:
  - polynomial_degree: integer
    constraints:
      - value_range: 3~5 (多項式最高次數)
  - coefficients: list of integer
    constraints:
      - value_range: -10~10 (係數範圍)
      - 非零: 至少一個非零係數
      - leading_coefficient_non_zero: 確保最高次項係數不為零
  - derivative_order_1: integer
    constraints:
      - value_range: 1~3 (求導次數，如 f', f'', f''')
      - less_than_polynomial_degree: derivative_order_1 < polynomial_degree
  - derivative_order_2: integer
    constraints:
      - value_range: 1~3 (求導次數，如 f', f'', f''')
      - less_than_polynomial_degree: derivative_order_2 < polynomial_degree
    mutually_exclusive_with: [derivative_order_1] # 兩次求導的次數不能相同

operators:
  - +, -, *, ^ (指數)
  - derivative (求導運算)

constraints:
  - 可計算性: 所有中間值與最終答案的係數都必須「可精確計算」（用 int）
  - 邊界:
    * 整數範圍: 原始係數範圍 -10~10
    * 運算複雜度: 最終答案多項式中的係數絕對值不超過 3 位數（例: 120, -360）
  - 最小複雜度:
    * 原始多項式必須至少有 3 個非零項。
    * 原始多項式次數必須至少為 3。
    * 必須要求計算兩個不同次數的導數。

templates:
  - name: polynomial_multiple_derivatives

    complexity_requirements: |
      - 原始多項式次數 (polynomial_degree) 必須在 3 到 5 之間。
      - 原始多項式必須包含至少 3 個非零項（不含常數項）。
      - 必須要求計算兩個不同次數的導數 (derivative_order_1, derivative_order_2)。
      - 兩個導數的次數都必須小於原始多項式次數。
      - 最終導數的係數絕對值不應超過 3 位數。

    variables:
      - degree: 隨機選取 3~5 之間的整數。
      - coeffs: 生成 `degree + 1` 個整數，範圍 -10~10。
        * 確保 `coeffs[0]` (最高次項係數) 非零。
        * 確保至少有 3 個非零元素（不包含常數項）。
      - order1: 隨機選取 1~3 之間的整數，且 `order1 < degree`。
      - order2: 隨機選取 1~3 之間的整數，且 `order2 < degree`，並確保 `order2 != order1`。

    ⚠️ **關鍵：數據格式轉換（必須執行）**:
      標準函數庫的所有多項式函數（_poly_to_latex, _differentiate_poly 等）使用 **terms 格式**：
        terms = [(coeff, exp), ...]  例如 [(3, 2), (-5, 1), (2, 0)] 表示 3x² - 5x + 2
      
      但你生成的 coeffs 是 **係數列表格式**：
        coeffs = [3, -5, 2]  (降冪排列)
      
      🔴 **必須先轉換格式，才能調用函數**：
      ```python
      # Step 1: 生成係數列表（降冪）
      coeffs = [3, -5, 2]  # 表示 3x² - 5x + 2
      
      # Step 2: 轉換為 terms 格式（使用標準函數）
      terms = _coeffs_to_terms(coeffs)  # 得到 [(3, 2), (-5, 1), (2, 0)]
      
      # Step 3: 調用多項式函數
      poly_latex = _poly_to_latex(terms)           # ✅ 正確
      deriv_terms = _differentiate_poly(terms, 1)  # ✅ 正確
      deriv_str = _poly_to_plain(deriv_terms)      # ✅ 正確
      
      # ❌ 錯誤示範（不要這樣做）：
      # poly_latex = _poly_to_latex(coeffs)  # ❌ TypeError!
      ```

    construction: |
      1. 生成 coeffs = [a_n, a_{n-1}, ..., a_0] (降冪排列)
      2. **轉換格式**: terms = _coeffs_to_terms(coeffs)
      3. 計算導數:
         - deriv1_terms = _differentiate_poly(terms, order=order1)
         - deriv2_terms = _differentiate_poly(terms, order=order2)
      4. 組裝題目:
         - poly_str = _poly_to_latex(terms)
         - q = f'已知 $f(x) = {poly_str}$，求 ... 的導數。'
      5. 組裝答案（見下方格式規範）

    ⚠️ **答案格式規範（CRITICAL - 違反會導致驗證失敗）**:
      
      ✅ **正確格式**（純多項式，逗號分隔，無符號無換行）：
      ```python
      # 範例：求 f'(x) 和 f''(x)
      deriv1_str = _poly_to_plain(deriv1_terms)  # 例如 "6x^2-10x"
      deriv2_str = _poly_to_plain(deriv2_terms)  # 例如 "12x-10"
      
      correct_answer = f"{deriv1_str}, {deriv2_str}"
      # 結果: "6x^2-10x, 12x-10"
      ```
      
      ❌ **錯誤格式**（包含導數符號或等號）：
      ```python
      # 不要這樣做：
      ans = f"f'(x) = {deriv1_str}\\nf''(x) = {deriv2_str}"  # ❌ 錯誤！
      ans = f"{_deriv_symbol_plain(1)} = {deriv1_str}"      # ❌ 錯誤！
      ```
      
      **答案驗證邏輯**：
      - 系統只接受純多項式字符串，例如 "3x^2-5, 6x"
      - 如果包含 "f'(x)" 或 "=" 或換行符，驗證會失敗
      - 多個導數用逗號+空格分隔: ", "

    example_implementation: |
      ```python
      def generate(level=1, **kwargs):
          # Step 1: 生成參數
          degree = random.randint(3, 5)
          coeffs = [random.randint(-10, 10) for _ in range(degree + 1)]
          while coeffs[0] == 0:
              coeffs[0] = random.randint(1, 10)
          
          # 確保至少 3 個非零項
          non_zero_count = sum(c != 0 for c in coeffs[:-1])
          while non_zero_count < 3:
              idx = random.randint(1, degree - 1)
              if coeffs[idx] == 0:
                  coeffs[idx] = random.randint(-10, 10)
                  non_zero_count += 1
          
          # Step 2: 選擇求導次數
          order1 = random.randint(1, min(3, degree - 1))
          order2 = random.randint(1, min(3, degree - 1))
          while order2 == order1:
              order2 = random.randint(1, min(3, degree - 1))
          
          # Step 3: 🔴 格式轉換（關鍵步驟）
          terms = _coeffs_to_terms(coeffs)
          
          # Step 4: 計算導數
          deriv1_terms = _differentiate_poly(terms, order=order1)
          deriv2_terms = _differentiate_poly(terms, order=order2)
          
          # Step 5: 組裝題目
          poly_latex = _poly_to_latex(terms)
          deriv1_sym = _deriv_symbol_latex(order1)  # 例如 "f'(x)"
          deriv2_sym = _deriv_symbol_latex(order2)  # 例如 "f''(x)"
          
          q = f'已知 $f(x) = {poly_latex}$，求 ${deriv1_sym}$ 與 ${deriv2_sym}$。'
          
          # Step 6: 🔴 組裝答案（正確格式）
          deriv1_str = _poly_to_plain(deriv1_terms)
          deriv2_str = _poly_to_plain(deriv2_terms)
          
          # ✅ 正確：純多項式，逗號分隔
          correct_answer = f"{deriv1_str}, {deriv2_str}"
          
          return {
              'question_text': q,
              'correct_answer': correct_answer,
              'answer': correct_answer,
              'mode': 1
          }
      ```

    禁止代碼生成模式:
      ❌ 禁止在代碼結尾添加任何說明文字（中文或英文）
      ❌ 禁止在答案中包含導數符號（如 "f'(x) ="）
      ❌ 禁止在答案中使用換行符 \\n 分隔多個導數
      ❌ 禁止調用 clean_latex_output(q) 處理已包含 $ 符號的題目
      ❌ 禁止使用 while 迴圈生成不重複隨機數（用 shuffle + slice）

answer_spec:
  format: "polynomial1, polynomial2"  # 純多項式，逗號分隔，無空格於運算符
  examples:
    - "6x^2-10x, 12x-10"        # f'(x) 和 f''(x)
    - "35x^4-24x^2, 140x^3-48x" # f'(x) 和 f''(x)
    - "3x^2, 6x"                 # 簡單情況
  forbidden:
    - "f'(x) = 6x^2-10x\\nf''(x) = 12x-10"  # ❌ 包含符號和換行
    - "f'(x) = 6x^2-10x, f''(x) = 12x-10"   # ❌ 包含符號
    - "6x^2 - 10x, 12x - 10"                # ❌ 包含空格（雖然可能通過驗證，但不標準）
```

🔴 **三大核心規則（必須記住）**:
1. **格式轉換**: coeffs → terms (使用 _coeffs_to_terms)
2. **答案格式**: 純多項式，逗號分隔，無符號無換行
3. **題目組裝**: 手動添加 $ 符號，不要用 clean_latex_output
"""

def update_master_spec():
    conn = sqlite3.connect('instance/kumon_math.db')
    cur = conn.cursor()
    
    # 插入新的 MASTER_SPEC
    cur.execute('''
        INSERT INTO skill_gencode_prompt (skill_id, prompt_content, created_at)
        VALUES (?, ?, datetime('now'))
    ''', (skill_id, NEW_MASTER_SPEC))
    
    new_id = cur.lastrowid
    conn.commit()
    
    print(f"✅ 新 MASTER_SPEC 已插入")
    print(f"   ID: {new_id}")
    print(f"   長度: {len(NEW_MASTER_SPEC):,} chars")
    print(f"   技能: {skill_id}")
    
    # 驗證
    latest = cur.execute(
        'SELECT id, LENGTH(prompt_content) FROM skill_gencode_prompt WHERE skill_id=? ORDER BY id DESC LIMIT 1',
        (skill_id,)
    ).fetchone()
    
    print(f"\n✅ 驗證：最新 MASTER_SPEC")
    print(f"   ID: {latest[0]}")
    print(f"   長度: {latest[1]:,} chars")
    
    conn.close()

if __name__ == '__main__':
    update_master_spec()
