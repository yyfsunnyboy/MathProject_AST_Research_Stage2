# Skill: jh_數學2上_FourArithmeticOperationsOfPolynomial

## [DOMAIN_API]
- `PolynomialOps.normalize(coeffs)`: 移除前導零。
- `PolynomialOps.format_latex(coeffs, var='x')`: 標準 LaTeX（帶 `^{n}`，自動省略係數 1）。
- `PolynomialOps.format_plain(coeffs, var='x')`: 純文字答案（無空格）。
- `PolynomialOps.add(c1, c2)`: 加法。
- `PolynomialOps.sub(c1, c2)`: 減法。
- `PolynomialOps.mul(c1, c2)`: 乘法。
- `PolynomialOps.random_poly(degree, range_val=(-5,5))`: 隨機係數（最高項非零）。

## [NUMERICAL_SPEC]
- 變數只能使用小寫 `'x'`。
- 使用 **係數列表（降冪順序）** 表示多項式（例如：`[3, -2, 1]` = `3x^{2} - 2x + 1`）。
- **絕對禁止** 字串拼接計算（例如 `"3x^2" + "2x"` 是錯的），所有數學操作必須透過 `PolynomialOps.add / sub / mul` 處理 `coeffs` 陣列。
- **題目呈現** 必須用 `PolynomialOps.format_latex(coeffs, var)` 包裝為 LaTeX 格式。
- **答案產出** 必須用 `PolynomialOps.format_plain(coeffs, var)` 成為簡潔字串。
- **標點符號**：題目中的逗號必須使用**全形逗號** `，`（嚴禁使用半形 `,`），結尾使用 `。`。
- **LaTeX 規範**：所有多項式式子必須用雙錢幣符號 `$$...$$` 包裹。嚴禁出現 `/` 除號，除非是 LaTeX 命令。禁止印出含係數 `1` 的 `1x`（交給 `format_latex` 處理）。
- **[⚠️ 格式轉換命令]**：即使例題或 MASTER_SPEC 寫成 `x2`，你也必須具備基礎數學常識，強制將其轉換為標準的 LaTeX 格式 `x^{2}`，並交由 `PolynomialOps.format_latex` 進行渲染。

## [LEGACY_CODE_DNA]
```python
import random

def generate(level=1, **kwargs):
    var = 'x'

    if level == 1:
        # 加減法
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
        # 乘法展開
        coeffs_a = PolynomialOps.random_poly(1)
        coeffs_b = PolynomialOps.random_poly(2)
        result_coeffs = PolynomialOps.mul(coeffs_a, coeffs_b)
        a_latex = PolynomialOps.format_latex(coeffs_a, var)
        b_latex = PolynomialOps.format_latex(coeffs_b, var)
        question_text = f'展開並化簡 $({a_latex})({b_latex})$。'
        correct_answer = PolynomialOps.format_plain(result_coeffs, var)

    else:  # level 3
        # 求未知多項式 P
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
