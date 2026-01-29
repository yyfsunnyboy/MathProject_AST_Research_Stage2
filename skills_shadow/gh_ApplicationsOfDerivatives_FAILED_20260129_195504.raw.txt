```python
from random import randint, choice
from fractions import Fraction

def fmt_num(x):
    if isinstance(x, int) and x < 0:
        return f"({x})"
    elif isinstance(x, Fraction) and x.denominator == 1:
        return str(x.numerator)
    else:
        return f"{x}"

def format_linear_factor(coeff, const, var='x'):
    if coeff == 1:
        linear_part = var
    elif coeff == -1:
        linear_part = f"-{var}"
    else:
        linear_part = f"{fmt_num(coeff)}{var}"
    
    if const > 0:
        return f"({linear_part}+{const})"
    elif const < 0:
        return f"({linear_part}{const})"
    else:
        return f"({linear_part})"

def format_coefficient(value):
    if value == 1:
        return ""
    elif value == -1:
        return "-"
    elif isinstance(value, Fraction) and value.denominator == 1:
        return str(value.numerator)
    else:
        return fmt_num(value)

def format_constant(value):
    if value > 0:
        return f"+ {value}"
    elif value < 0:
        return f"- {-value}"
    else:
        return ""

def clean_latex_output(text):
    # 簡單的清洗，確保 $ 符號正確
    if text.startswith('$') and text.endswith('$'):
        return text
    return f"${text}$"

def generate(level=1, **kwargs):
    while True:
        f_x_poly1_coeff = choice([-3, -2, -1, 1, 2, 3])
        f_x_poly1_const = randint(-5, 5)
        f_x_poly2_coeff = choice([-3, -2, -1, 1, 2, 3])
        f_x_poly2_const = randint(-5, 5)
        f_x_poly2_power = choice([2, 3, 4])
        x_tangent = randint(-3, 3)

        # 確保 A 和 C 非零
        if f_x_poly1_coeff == 0 or f_x_poly2_coeff == 0:
            continue

        # 定義函數 f(x)
        def f_x(x):
            return (f_x_poly1_coeff * x + f_x_poly1_const) * ((f_x_poly2_coeff * x + f_x_poly2_const) ** f_x_poly2_power)

        # 計算導函數 f'(x)
        def u_prime(x):
            return f_x_poly1_coeff

        def v_prime(x):
            h_prime = f_x_poly2_coeff
            g_prime = f_x_poly2_power * ((f_x_poly2_coeff * x + f_x_poly2_const) ** (f_x_poly2_power - 1))
            return g_prime * h_prime

        def f_prime(x):
            u = f_x_poly1_coeff * x + f_x_poly1_const
            v = (f_x_poly2_coeff * x + f_x_poly2_const) ** f_x_poly2_power
            return u_prime(x) * v + u * v_prime(x)

        # 計算切點 y_tangent
        y_tangent = f_x(x_tangent)
        m = f_prime(x_tangent)

        # 確保斜率不為零且符合複雜度要求
        if m == 0 or abs(m.numerator) > 999 or abs(m.denominator) > 999:
            continue

        # 計算截距 k
        k = y_tangent - m * x_tangent

        # 確保截距符合複雜度要求
        if abs(k.numerator) > 999 or abs(k.denominator) > 999:
            continue

        # 格式化答案
        m_str = format_coefficient(m)
        k_str = format_constant(k)

        if m == 0:
            ans_str = f"y = {k_str.strip('+ ')}"
        elif k == 0:
            ans_str = f"y = {m_str}x"
        else:
            ans_str = f"y = {m_str}x {k_str}"

        # 格式化問題描述
        poly1_str = format_linear_factor(f_x_poly1_coeff, f_x_poly1_const, 'x')
        poly2_base_str = format_linear_factor(f_x_poly2_coeff, f_x_poly2_const, 'x')
        f_x_latex = f"{poly1_str}{poly2_base_str}^{{{fmt_num(f_x_poly2_power)}}}"
        point_latex = f"P({fmt_num(x_tangent)}, {fmt_num(y_tangent)})"
        q_str = f"在函數 $f(x) = {f_x_latex}$ 的圖形上，求以點 ${point_latex}$ 為切點的切線方程式。"
        question_output = clean_latex_output(q_str)

        return {'question_text': question_output, 'answer': ans_str, 'mode': 1}

# Example usage:
# print(generate())
```