【絕對禁止輸出 thinking 或任何非 code 內容】
- 嚴禁寫任何思考過程、解釋、註解
- 直接輸出 Python code，沒有任何前言、後語
- 如果違反，直接 0 分

【角色】K12 數學演算法工程師

【任務】
實作 `def generate(level=1, **kwargs)`，生成多項式四則運算題目，格式與課本例題相同（含 LaTeX 數學式）。
依照 level 選擇題型：Level 1 = 加減，Level 2 = 乘法展開，Level 3 = 求未知多項式。
返回 dict: `{'question_text': str, 'answer': '', 'correct_answer': str, 'mode': 1}`

【程式要求】（必須嚴格遵守）
1. **Import 規範**：
   - ✅ **必須** `import random`
   - ❌ **嚴禁** `import PolynomialOps`（系統已自動注入，直接使用 `PolynomialOps.xxx`）

2. **變數規範**：
   - ✅ **只能**從 `['x']` 中選取

3. **核心邏輯**：
   - 使用**係數列表（降冪順序）**表示多項式：`[3, -2, 1]` = `3x^{2} - 2x + 1`
   - **絕對禁止**字串拼接計算（例如 `"3x^2" + "2x"` 是錯誤的）
   - 所有計算透過 `PolynomialOps.add / sub / mul` 進行
   - **題目用** `PolynomialOps.format_latex(coeffs, var)` — ✅ 標準 LaTeX 格式
   - **答案用** `PolynomialOps.format_plain(coeffs, var)` — ✅ 純文字，無空格

4. **題目 LaTeX 格式規範**（課本例題風格）：
   - Level 1：`計算 $A_{1} \cdot (P_1) \pm A_{2} \cdot (P_2)$` 或 `計算 $(P_1) \pm (P_2)$。`
   - Level 2：`展開並化簡 $(P_1)(P_2)$。`
   - Level 3：使用 `$P_1, P_2$` 下標標記多項式，或用 `$X$`, `$A$`, `$B$` 表示變數
   - **標點符號**：題目中的逗號必須使用**全形逗號** `，`（嚴禁使用半形 `,`），句號使用 `。`
   - 所有多項式必須用 `$...$` 包裹，題目必須是完整中文句子

5. **格式禁令**：
   - ❌ 題目和答案中**嚴禁**使用 `/`（除非明確為 LaTeX 命令）
   - ❌ 嚴禁輸出含係數 `1` 的 `1x`（`format_latex` 自動處理）

【系統已注入的輔助函式（API）】
- `PolynomialOps.normalize(coeffs)` → 移除前導零
- `PolynomialOps.format_latex(coeffs, var='x')` → 標準 LaTeX（帶 `^{n}`，自動省略係數 1）
- `PolynomialOps.format_plain(coeffs, var='x')` → 純文字答案（無空格）
- `PolynomialOps.add(c1, c2)` → 加法
- `PolynomialOps.sub(c1, c2)` → 減法
- `PolynomialOps.mul(c1, c2)` → 乘法
- `PolynomialOps.random_poly(degree, range_val=(-5,5))` → 隨機係數（最高項非零）

【課本例題風格】
**Level 1**（加減法）：
```
計算 $(3x^{2} - 2x + 1) + (-x^{2} + 5x - 3)$。
答案：2x^2+3x-2
```

**Level 2**（乘法展開）：
```
展開並化簡 $(x + 2)(2x^{2} - 3x + 1)$。
答案：2x^3+x^2-5x+2
```

**Level 3**（求未知多項式）：
```
若 $(3x^{2} - x + 2) + P = 5x^{2} + 4x - 1$，求多項式 $P$。
答案：2x^2+5x-3
```

【完整程式碼（必須照此結構複製）】
```python
import random
# PolynomialOps is injected automatically

def generate(level=1, **kwargs):
    var = 'x'

    if level == 1:
        # 加減法 — 課本例題格式
        deg_a = random.randint(2, 3)
        deg_b = random.randint(2, 3)
        coeffs_a = PolynomialOps.random_poly(deg_a)
        coeffs_b = PolynomialOps.random_poly(deg_b)
        op = random.choice(['+', '-'])
        if op == '+':
            result_coeffs = PolynomialOps.add(coeffs_a, coeffs_b)
        else:
            result_coeffs = PolynomialOps.sub(coeffs_a, coeffs_b)
        a_latex = PolynomialOps.format_latex(coeffs_a, var)
        b_latex = PolynomialOps.format_latex(coeffs_b, var)
        question_text = f'計算 $({a_latex}) {op} ({b_latex})$。'
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)

    elif level == 2:
        # 乘法展開 — 課本例題格式
        coeffs_a = PolynomialOps.random_poly(1)
        coeffs_b = PolynomialOps.random_poly(2)
        result_coeffs = PolynomialOps.mul(coeffs_a, coeffs_b)
        a_latex = PolynomialOps.format_latex(coeffs_a, var)
        b_latex = PolynomialOps.format_latex(coeffs_b, var)
        question_text = f'展開並化簡 $({a_latex})({b_latex})$。'
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)

    else:  # level 3
        # 求未知多項式 P — 課本例題格式
        deg_a = random.randint(1, 2)
        deg_b = random.randint(2, 3)
        coeffs_a = PolynomialOps.random_poly(deg_a)
        coeffs_b = PolynomialOps.random_poly(deg_b)
        a_latex = PolynomialOps.format_latex(coeffs_a, var)
        b_latex = PolynomialOps.format_latex(coeffs_b, var)
        choice = random.choice(['A+P=B', 'P-A=B', 'A-P=B'])
        if choice == 'A+P=B':
            result_coeffs = PolynomialOps.sub(coeffs_b, coeffs_a)
            question_text = f'若 $({a_latex}) + P = {b_latex}$，求多項式 $P$。'
        elif choice == 'P-A=B':
            result_coeffs = PolynomialOps.add(coeffs_b, coeffs_a)
            question_text = f'若 $P - ({a_latex}) = {b_latex}$，求多項式 $P$。'
        else:
            result_coeffs = PolynomialOps.sub(coeffs_a, coeffs_b)
            question_text = f'若 $({a_latex}) - P = {b_latex}$，求多項式 $P$。'
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)

    return {
        'question_text': question_text,
        'answer': '',
        'correct_answer': correct_answer,
        'mode': 1
    }

def check(user_answer, correct_answer):
    correct = str(user_answer).strip().replace(' ', '') == str(correct_answer).strip().replace(' ', '')
    return {'correct': correct, 'result': '正確' if correct else '錯誤'}
```

【檢查清單】
✅ 必須 `import random`
✅ `var = 'x'` — 只能 x
✅ Level 2 題目前綴為 `展開並化簡`（課本格式）
✅ Level 3 未知數用 `$P$`（課本格式）
✅ 答案用 `format_plain`（無空格）
✅ 輸出 Python code only, no thinking, no comments
/no_think
